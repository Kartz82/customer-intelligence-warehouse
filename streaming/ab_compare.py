"""Honest A/B: offline (rules-only) vs Gemini-assisted, over the SAME landed
events. Reads raw_orders_events, re-runs the clean gate in each mode, and reports
how many events the LLM rescues from quarantine.

    python -m streaming.ab_compare
"""
from __future__ import annotations

import copy
import json
from dataclasses import replace

import psycopg2

from streaming.ai_clean import OrderCleaner
from streaming.settings import Settings, load_settings


def _count_promoted(payloads: list[dict], settings: Settings) -> int:
    cleaner = OrderCleaner(settings)
    return sum(1 for p in payloads if cleaner.clean(copy.deepcopy(p)).accepted)


def main() -> None:
    base = load_settings()
    with psycopg2.connect(base.db_url) as conn, conn.cursor() as cur:
        cur.execute("SELECT payload FROM raw_orders_events ORDER BY event_id")
        payloads = [row[0] if isinstance(row[0], dict) else json.loads(row[0])
                    for row in cur.fetchall()]

    n = len(payloads)
    offline = _count_promoted(payloads, replace(base, provider="offline"))
    gemini = _count_promoted(payloads, base) if base.provider == "gemini" else offline

    print(f"landed events      : {n}")
    print(f"offline promoted   : {offline}  ({100*offline/n:.1f}%)")
    print(f"gemini  promoted   : {gemini}  ({100*gemini/n:.1f}%)")
    print(f"LLM rescued        : {gemini - offline} events "
          f"(+{100*(gemini-offline)/n:.1f} pts accept rate)")


if __name__ == "__main__":
    main()
