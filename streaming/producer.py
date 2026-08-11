"""Live order-event producer.

Emits a stream of *operational* order events to Redpanda (Kafka API) — the kind
of messy real-world payload an Analytics Engineer actually ingests: mixed date
formats, inconsistent status casing, dirty customer identifiers, money as strings.

Self-contained: generates synthetic-but-realistic events, no data file required,
so it runs free/offline and in CI. Rate is configurable.

Usage:
    python -m streaming.producer --rate 5 --count 500
    python -m streaming.producer --rate 2            # run until interrupted
"""
from __future__ import annotations

import argparse
import json
import random
import time
import uuid
from datetime import datetime, timedelta

from confluent_kafka import Producer

from streaming.settings import load_settings

# --- deliberately messy variants: this is what the AI-clean gate must handle ---
# Grouped by which layer should resolve them:
STATUS_VARIANTS = [
    # rule-resolvable (casing / known synonym / whitespace)
    "Complete", "completed", "COMPLETED", "complete ",
    "shipped", "Shipped", "SHIPPED",
    "cancelled", "Cancelled", "canceled",   # US/UK spelling drift
    # typos the rules miss but an LLM can map -> shows real LLM value
    "shipd", "shpped", "completd", "complete!!", "cancelld", "canceld",
    # genuinely unmappable -> LLM should ABSTAIN (quarantine)
    "pending", "on hold",
]
DATE_FORMATS = ["%m/%d/%y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]
COUNTRIES = ["United Kingdom", "France", "Germany", "EIRE", "Spain", "Netherlands"]
STOCK_CODES = ["85123A", "71053", "84406B", "22423", "47566", "21730", "POST"]


def _messy_customer_id(base: int) -> str:
    """Return the same customer in one of several inconsistent encodings."""
    style = random.choice(["C-{}", "C{}", "{}", " {} "])
    return style.format(base)


def _messy_amount(value: float) -> str | float:
    """Half the time emit money as a formatted string ('$1,249.00')."""
    if random.random() < 0.5:
        return f"${value:,.2f}"
    return round(value, 2)


def make_event() -> dict:
    """Build one deliberately-dirty order event."""
    order_dt = datetime(2026, 1, 8) + timedelta(days=random.randint(0, 40))
    qty = random.choice([1, 1, 2, 3, 5, -1])           # -1 = a return
    return {
        "order_id": f"10{random.randint(1000, 9999)}",
        "cust_id": _messy_customer_id(random.randint(100, 260)),
        "order_date": order_dt.strftime(random.choice(DATE_FORMATS)),
        "amount": _messy_amount(random.uniform(5, 1500)),
        "qty": qty,
        "status": random.choice(STATUS_VARIANTS),
        "stock_code": random.choice(STOCK_CODES),
        "country": random.choice(COUNTRIES),
        "emitted_at": datetime.utcnow().isoformat(),
        "trace": str(uuid.uuid4()),
    }


def _delivery_report(err, msg) -> None:
    if err is not None:
        print(f"delivery failed: {err}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Order-event stream producer")
    ap.add_argument("--rate", type=float, default=5.0, help="events per second")
    ap.add_argument("--count", type=int, default=0, help="0 = run until Ctrl-C")
    args = ap.parse_args()

    cfg = load_settings()
    producer = Producer({"bootstrap.servers": cfg.bootstrap_servers})
    topic = cfg.topic
    interval = 1.0 / args.rate if args.rate > 0 else 0

    print(f"producing to {cfg.bootstrap_servers} topic={topic} rate={args.rate}/s")
    sent = 0
    try:
        while args.count == 0 or sent < args.count:
            event = make_event()
            producer.produce(
                topic,
                key=event["order_id"],
                value=json.dumps(event).encode("utf-8"),
                callback=_delivery_report,
            )
            producer.poll(0)
            sent += 1
            if sent % 50 == 0:
                print(f"  sent {sent} events")
            if interval:
                time.sleep(interval)
    except KeyboardInterrupt:
        print("\ninterrupted")
    finally:
        producer.flush(10)
        print(f"done. total sent={sent}")


if __name__ == "__main__":
    main()
