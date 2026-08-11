"""Stream consumer: Redpanda -> land -> AI-clean -> promote/quarantine (PostgreSQL).

For every event:
  1. land the raw payload in raw_orders_events (append-only, nothing lost)
  2. run the AI-clean gate
  3. write the full decision audit trail
  4. promote to fact_orders_stream  OR  quarantine  (abstention)

Invariant enforced downstream by dbt: landed == promoted + quarantined.

Usage:
    python -m streaming.consumer --batch 500   # consume 500 then exit (CI)
    python -m streaming.consumer               # run until Ctrl-C
"""
from __future__ import annotations

import argparse
import json

import psycopg2
from confluent_kafka import Consumer, KafkaException
from psycopg2.extras import Json

from streaming.ai_clean import CleanResult, OrderCleaner
from streaming.settings import load_settings


def _land(cur, cfg_topic: str, msg) -> int:
    payload = json.loads(msg.value().decode("utf-8"))
    cur.execute(
        """INSERT INTO raw_orders_events (source, kafka_topic, kafka_offset, payload)
           VALUES (%s, %s, %s, %s) RETURNING event_id""",
        ("redpanda", cfg_topic, msg.offset(), Json(payload)),
    )
    event_id = cur.fetchone()[0]
    return event_id, payload


def _write_audits(cur, event_id: int, result: CleanResult) -> None:
    for a in result.audits:
        cur.execute(
            """INSERT INTO orders_clean_audit
               (event_id, field, raw_value, clean_value, method, confidence, model)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (event_id, a.field, a.raw_value, a.clean_value, a.method, a.confidence, a.model),
        )


def _promote(cur, event_id: int, row: dict) -> None:
    cur.execute(
        """INSERT INTO fact_orders_stream
           (event_id, order_id, customer_id, country, stock_code, quantity,
            unit_price, order_status, order_ts, line_revenue)
           VALUES (%(event_id)s, %(order_id)s, %(customer_id)s, %(country)s,
                   %(stock_code)s, %(quantity)s, %(unit_price)s, %(order_status)s,
                   %(order_ts)s, %(line_revenue)s)""",
        {**row, "event_id": event_id},
    )


def _quarantine(cur, event_id: int, payload: dict, result: CleanResult) -> None:
    cur.execute(
        """INSERT INTO orders_quarantine
           (event_id, reason, field, raw_value, payload)
           VALUES (%s, %s, %s, %s, %s)""",
        (event_id, result.quarantine_reason, result.quarantine_field,
         result.quarantine_value, Json(payload)),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Order-event AI-clean consumer")
    ap.add_argument("--batch", type=int, default=0, help="0 = run until Ctrl-C")
    args = ap.parse_args()

    cfg = load_settings()
    cleaner = OrderCleaner(cfg)
    print(f"ai-clean provider={cfg.provider} model={cfg.model} "
          f"threshold={cfg.confidence_threshold}")

    conn = psycopg2.connect(cfg.db_url)
    conn.autocommit = False

    consumer = Consumer({
        "bootstrap.servers": cfg.bootstrap_servers,
        "group.id": cfg.group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([cfg.topic])
    print(f"consuming {cfg.topic} from {cfg.bootstrap_servers}")

    processed = promoted = quarantined = 0
    try:
        while args.batch == 0 or processed < args.batch:
            msg = consumer.poll(1.0)
            if msg is None:
                if args.batch:            # batch mode: stop when stream drains
                    break
                continue
            if msg.error():
                raise KafkaException(msg.error())

            with conn.cursor() as cur:
                event_id, payload = _land(cur, cfg.topic, msg)
                result = cleaner.clean(payload)
                _write_audits(cur, event_id, result)
                if result.accepted:
                    _promote(cur, event_id, result.row)
                    promoted += 1
                else:
                    _quarantine(cur, event_id, payload, result)
                    quarantined += 1
            conn.commit()
            consumer.commit(msg)
            processed += 1
            if processed % 50 == 0:
                print(f"  processed={processed} promoted={promoted} quarantined={quarantined}")
    except KeyboardInterrupt:
        print("\ninterrupted")
    finally:
        consumer.close()
        conn.close()
        rate = (promoted / processed * 100) if processed else 0
        print(f"done. processed={processed} promoted={promoted} "
              f"quarantined={quarantined} accept_rate={rate:.1f}%")


if __name__ == "__main__":
    main()
