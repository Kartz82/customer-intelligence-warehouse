"""Shared settings for the streaming layer, sourced from config/config.yaml + env.

Secrets (GEMINI_API_KEY) come from the environment only, never from config files.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv optional
    pass


@dataclass(frozen=True)
class Settings:
    # kafka / redpanda
    bootstrap_servers: str
    topic: str
    group_id: str
    # postgres
    db_url: str
    # ai-clean
    provider: str            # 'gemini' | 'offline'
    model: str
    confidence_threshold: float
    min_call_interval_s: float   # throttle to stay under free-tier RPM (0 = off)
    gemini_api_key: str | None


def load_settings(config_path: str = "config/config.yaml") -> Settings:
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    db = cfg["database"]
    db_url = (
        f"postgresql://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['db_name']}"
    )

    kafka = cfg.get("kafka", {})
    ai = cfg.get("ai_clean", {})

    key = os.getenv("GEMINI_API_KEY")
    provider = ai.get("provider", "gemini")
    # No key -> silently fall back to offline (rules-only). Keeps it free/CI-safe.
    if provider == "gemini" and not key:
        provider = "offline"

    return Settings(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", kafka.get("bootstrap_servers", "localhost:19092")),
        topic=kafka.get("topic", "raw_orders"),
        group_id=kafka.get("group_id", "orders-cleaner"),
        db_url=db_url,
        provider=provider,
        model=os.getenv("GEMINI_MODEL", ai.get("model", "gemini-flash-lite-latest")),
        confidence_threshold=float(ai.get("confidence_threshold", 0.85)),
        min_call_interval_s=float(ai.get("min_call_interval_s", 0)),
        gemini_api_key=key,
    )
