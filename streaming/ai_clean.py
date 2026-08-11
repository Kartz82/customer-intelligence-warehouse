"""AI-clean gate: deterministic rules first, LLM only on genuine ambiguity,
abstain (quarantine) when confidence is below threshold.

Design principle — the pipeline is allowed to say "I don't know":
  * high-confidence normalisation  -> apply via RULE  (free, deterministic)
  * genuine ambiguity              -> ask the LLM      (rare, cheap, Gemini free tier)
  * still not confident            -> QUARANTINE       (never guess silently)

Returns a CleanResult carrying the typed row, a full audit trail of every
decision, and — if the event could not be trusted — a quarantine reason.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from streaming.settings import Settings

# Canonical, closed vocabulary the warehouse commits to.
CANONICAL_STATUS = {"completed", "shipped", "cancelled"}
STATUS_RULES = {
    "complete": "completed",
    "completed": "completed",
    "shipped": "shipped",
    "cancelled": "cancelled",
    "canceled": "cancelled",   # US spelling -> UK canonical
}
REVENUE_STATUSES = {"completed", "shipped"}   # cancelled excluded from revenue


@dataclass
class AuditRecord:
    field: str
    raw_value: str
    clean_value: str | None
    method: str            # 'rule' | 'llm' | 'passthrough'
    confidence: float
    model: str | None = None


@dataclass
class CleanResult:
    row: dict[str, Any] | None                     # promoted typed row, or None
    audits: list[AuditRecord] = field(default_factory=list)
    quarantine_reason: str | None = None
    quarantine_field: str | None = None
    quarantine_value: str | None = None

    @property
    def accepted(self) -> bool:
        return self.row is not None


# ------------------------------------------------------------------ rules ----

def clean_customer_id(raw: Any) -> tuple[int | None, AuditRecord]:
    s = str(raw).strip()
    digits = re.sub(r"[^0-9]", "", s)          # 'C-193', 'C193', ' 193 ' -> '193'
    if digits:
        return int(digits), AuditRecord("customer_id", s, digits, "rule", 1.0)
    return None, AuditRecord("customer_id", s, None, "rule", 0.0)


def clean_amount(raw: Any) -> tuple[float | None, AuditRecord]:
    s = str(raw).strip()
    cleaned = re.sub(r"[^0-9.\-]", "", s)      # '$1,249.00' -> '1249.00'
    try:
        return float(cleaned), AuditRecord("unit_price", s, cleaned, "rule", 1.0)
    except ValueError:
        return None, AuditRecord("unit_price", s, None, "rule", 0.0)


def clean_status_rule(raw: Any) -> AuditRecord | None:
    """Return a rule-based audit if the status is a known variant, else None."""
    s = str(raw).strip().lower()
    if s in STATUS_RULES:
        return AuditRecord("status", str(raw), STATUS_RULES[s], "rule", 1.0)
    return None


def parse_date_rule(raw: Any) -> AuditRecord | None:
    """Accept a date only when it is UNAMBIGUOUS. If day and month are both
    <= 12 the value is genuinely ambiguous (e.g. 01/08/26) -> defer (None)."""
    s = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return AuditRecord("order_ts", s, dt.date().isoformat(), "rule", 1.0)
        except ValueError:
            continue
    # slash m/d/y form is ambiguous when both parts <= 12
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a <= 12 and b <= 12 and a != b:
            return None                        # ambiguous -> LLM / abstain
        try:
            dt = datetime.strptime(s, "%m/%d/%y")
            return AuditRecord("order_ts", s, dt.date().isoformat(), "rule", 0.95)
        except ValueError:
            return None
    return None


# -------------------------------------------------------------------- llm ----

class GeminiJudge:
    """Thin Gemini REST wrapper (stdlib only — no SDK, no protobuf conflict).
    Returns (value, confidence). Never raises to caller."""

    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.gemini_api_key if settings.provider == "gemini" else None
        self._min_interval = settings.min_call_interval_s
        self._last_call = 0.0

    @property
    def online(self) -> bool:
        return bool(self.api_key)

    def _throttle(self) -> None:
        """Space calls out to stay under the free-tier RPM before we get 429'd."""
        if self._min_interval > 0:
            wait = self._min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
        self._last_call = time.monotonic()

    def resolve(self, prompt: str, retries: int = 3) -> tuple[str | None, float]:
        if not self.api_key:
            return None, 0.0
        self._throttle()
        url = self.ENDPOINT.format(model=self.settings.model) + f"?key={self.api_key}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(retries):
            try:
                req = urllib.request.Request(
                    url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    out = json.loads(resp.read().decode("utf-8"))
                text = out["candidates"][0]["content"]["parts"][0]["text"]
                data = _parse_json(text)
                val = data.get("value")
                # JSON null -> Python None (never the string 'None')
                clean = None if val is None else str(val)
                return clean, float(data.get("confidence", 0.0))
            except urllib.error.HTTPError as exc:
                # 429 rate limit / 5xx transient -> exponential backoff, then abstain
                if exc.code in (429, 500, 503) and attempt < retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                print(f"[ai_clean] LLM call failed: {exc}")
                return None, 0.0
            except Exception as exc:
                print(f"[ai_clean] LLM call failed: {exc}")
                return None, 0.0
        return None, 0.0


def _parse_json(text: str) -> dict:
    """Parse the first JSON object from a model reply, tolerating code fences
    and any trailing content (raw_decode stops at the end of the first value)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?|\n?```$", "", text).strip()
    start = text.find("{")
    if start > 0:
        text = text[start:]
    obj, _ = json.JSONDecoder().raw_decode(text)
    return obj


def _status_prompt(raw: str) -> str:
    return (
        "You normalise e-commerce order statuses. Map the value to exactly one of "
        "['completed','shipped','cancelled'], or null if it does not map. "
        'Reply ONLY JSON: {"value": <str|null>, "confidence": <0..1>}.\n'
        f"Value: {raw!r}"
    )


def _date_prompt(raw: str) -> str:
    return (
        "This date string is ambiguous (day/month order unknown). If you can infer "
        "the intended ISO date (YYYY-MM-DD) with high confidence return it, else null. "
        'Reply ONLY JSON: {"value": <YYYY-MM-DD|null>, "confidence": <0..1>}.\n'
        f"Value: {raw!r}"
    )


# --------------------------------------------------------------- pipeline ----

class OrderCleaner:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.judge = GeminiJudge(settings)
        self.threshold = settings.confidence_threshold

    def clean(self, payload: dict) -> CleanResult:
        audits: list[AuditRecord] = []

        # --- customer id (rule) ---
        cust, a = clean_customer_id(payload.get("cust_id"))
        audits.append(a)
        if cust is None:
            return CleanResult(None, audits, "unparseable customer id",
                               "customer_id", str(payload.get("cust_id")))

        # --- unit price (rule) ---
        price, a = clean_amount(payload.get("amount"))
        audits.append(a)
        if price is None or price < 0:
            return CleanResult(None, audits, "invalid amount",
                               "unit_price", str(payload.get("amount")))

        # --- status (rule -> llm -> abstain) ---
        status_audit = clean_status_rule(payload.get("status"))
        if status_audit is None:
            value, conf = self.judge.resolve(_status_prompt(str(payload.get("status"))))
            if value in CANONICAL_STATUS and conf >= self.threshold:
                status_audit = AuditRecord("status", str(payload.get("status")),
                                           value, "llm", conf, self.settings.model)
            else:
                return CleanResult(None, audits,
                                   f"unresolved status (conf={conf:.2f})",
                                   "status", str(payload.get("status")))
        audits.append(status_audit)

        # --- order date (rule -> llm -> abstain) ---
        date_audit = parse_date_rule(payload.get("order_date"))
        if date_audit is None:
            value, conf = self.judge.resolve(_date_prompt(str(payload.get("order_date"))))
            if value and conf >= self.threshold:
                date_audit = AuditRecord("order_ts", str(payload.get("order_date")),
                                         value, "llm", conf, self.settings.model)
            else:
                return CleanResult(None, audits,
                                   f"ambiguous date (conf={conf:.2f})",
                                   "order_ts", str(payload.get("order_date")))
        audits.append(date_audit)

        # --- quantity (rule) ---
        try:
            qty = int(payload.get("qty"))
        except (TypeError, ValueError):
            return CleanResult(None, audits, "invalid quantity",
                               "quantity", str(payload.get("qty")))

        status = status_audit.clean_value
        line_revenue = round(qty * price, 2) if status in REVENUE_STATUSES else 0.0

        row = {
            "order_id": str(payload.get("order_id"))[:40],
            "customer_id": cust,
            "country": str(payload.get("country", "")).strip()[:100],
            "stock_code": str(payload.get("stock_code", ""))[:40],
            "quantity": qty,
            "unit_price": price,
            "order_status": status,
            "order_ts": date_audit.clean_value,
            "line_revenue": line_revenue,
        }
        return CleanResult(row, audits)
