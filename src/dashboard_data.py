from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FACT_SALES_PATH = PROJECT_ROOT / "data" / "processed" / "fact_sales_enriched.csv"

RAW_WORKBOOK_ROWS = 1_067_371
README_CLEANED_ROWS = 1_062_984

OPERATIONAL_STOCK_CODES = {
    "M",
    "DOT",
    "D",
    "CRUK",
    "POST",
    "BANK CHARGES",
    "AMAZONFEE",
    "S",
}

OPERATIONAL_DESCRIPTION_PATTERN = re.compile(
    r"manual|postage|discount|commission|damage|damaged|damages|ebay|"
    r"amazon|bank charge|adjust|adjustment|found|lost|missing|"
    r"unsaleable|destroyed|samples?|mailout|check",
    flags=re.IGNORECASE,
)


def load_fact_sales(path: Path | str = FACT_SALES_PATH) -> pd.DataFrame:
    """Load the processed fact export used by the dashboard."""
    df = pd.read_csv(path)
    return clean_dashboard_fact(df)


def clean_dashboard_fact(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize types and add reusable dashboard metric columns."""
    cleaned = df.copy()
    cleaned["invoice_date"] = pd.to_datetime(cleaned["invoice_date"], errors="coerce")
    cleaned["month"] = cleaned["invoice_date"].dt.to_period("M").dt.to_timestamp()
    cleaned["customer_id"] = pd.to_numeric(cleaned["customer_id"], errors="coerce")
    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="coerce").fillna(0).astype(int)
    cleaned["unit_price"] = pd.to_numeric(cleaned["unit_price"], errors="coerce").fillna(0.0)
    cleaned["line_revenue"] = cleaned["quantity"] * cleaned["unit_price"]
    cleaned["is_return"] = cleaned["quantity"] < 0
    cleaned["is_positive_sale"] = cleaned["quantity"] > 0
    cleaned["gross_revenue"] = np.where(cleaned["quantity"] > 0, cleaned["line_revenue"], 0.0)
    cleaned["return_value"] = np.where(cleaned["quantity"] < 0, -cleaned["line_revenue"], 0.0)
    cleaned["positive_units"] = np.where(cleaned["quantity"] > 0, cleaned["quantity"], 0)
    cleaned["returned_units"] = np.where(cleaned["quantity"] < 0, -cleaned["quantity"], 0)
    cleaned["country_name"] = cleaned["country_name"].fillna("Unknown").astype(str)
    cleaned["stock_code"] = cleaned["stock_code"].fillna("Unknown").astype(str)
    cleaned["product_name"] = cleaned["product_name"].fillna("Unknown").astype(str)
    cleaned["is_cancel_invoice"] = cleaned["invoice_number"].astype(str).str.startswith("C")
    cleaned["is_operational_code"] = _operational_code_mask(cleaned)
    return cleaned


def filter_operational_codes(df: pd.DataFrame, include_operational: bool = False) -> pd.DataFrame:
    if include_operational:
        return df.copy()
    return df.loc[~df["is_operational_code"]].copy()


def filter_fact(
    df: pd.DataFrame,
    start_date: str | None = None,
    end_date: str | None = None,
    countries: list[str] | None = None,
) -> pd.DataFrame:
    filtered = df.copy()
    if start_date:
        filtered = filtered.loc[filtered["invoice_date"] >= pd.to_datetime(start_date)]
    if end_date:
        filtered = filtered.loc[filtered["invoice_date"] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    if countries:
        filtered = filtered.loc[filtered["country_name"].isin(countries)]
    return filtered


def get_executive_metrics(df: pd.DataFrame) -> dict[str, float]:
    positive = df.loc[df["quantity"] > 0]
    known_customer_orders = df.loc[df["customer_id"].notna()].groupby("customer_id")["invoice_number"].nunique()
    gross_revenue = float(df["gross_revenue"].sum())
    positive_invoices = positive["invoice_number"].nunique()
    return {
        "gross_revenue": gross_revenue,
        "net_revenue": float(df["line_revenue"].sum()),
        "return_value": float(df["return_value"].sum()),
        "total_units_sold": int(df["positive_units"].sum()),
        "active_customers": int(df["customer_id"].nunique(dropna=True)),
        "total_transactions": int(df["invoice_number"].nunique()),
        "average_order_value": gross_revenue / positive_invoices if positive_invoices else 0.0,
        "repeat_purchase_rate": (
            float((known_customer_orders > 1).mean()) if len(known_customer_orders) else 0.0
        ),
    }


def get_monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby("month", as_index=False)
        .agg(gross_revenue=("gross_revenue", "sum"), net_revenue=("line_revenue", "sum"))
        .sort_values("month")
    )
    return monthly


def get_customer_metrics(df: pd.DataFrame) -> dict[str, float]:
    customer_summary = _customer_summary(df)
    known = df["customer_id"].notna()
    return {
        "known_customers": int(df["customer_id"].nunique(dropna=True)),
        "guest_row_rate": float((~known).mean()) if len(df) else 0.0,
        "repeat_purchase_rate": float((customer_summary["order_count"] > 1).mean())
        if len(customer_summary)
        else 0.0,
        "median_ltv": float(customer_summary["lifetime_value"].median()) if len(customer_summary) else 0.0,
        "avg_order_frequency": float(customer_summary["order_count"].mean()) if len(customer_summary) else 0.0,
    }


def get_top_customers(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    return _customer_summary(df).sort_values("lifetime_value", ascending=False).head(n)


def get_customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    return _customer_summary(df)


def get_product_metrics(df: pd.DataFrame, include_operational: bool = False) -> dict[str, float]:
    product_df = filter_operational_codes(df, include_operational=include_operational)
    returned_units = float(product_df["returned_units"].sum())
    positive_units = float(product_df["positive_units"].sum())
    return {
        "product_count": int(product_df["stock_code"].nunique()),
        "units_sold": int(product_df["positive_units"].sum()),
        "returned_units": int(returned_units),
        "return_value": float(product_df["return_value"].sum()),
        "return_line_rate": float((product_df["quantity"] < 0).mean()) if len(product_df) else 0.0,
        "returned_unit_rate": returned_units / positive_units if positive_units else 0.0,
    }


def get_product_return_audit(
    df: pd.DataFrame,
    min_units: int = 1,
    include_operational: bool = False,
) -> pd.DataFrame:
    product_df = filter_operational_codes(df, include_operational=include_operational)
    audit = (
        product_df.groupby(["stock_code", "product_name"], as_index=False)
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            net_revenue=("line_revenue", "sum"),
            units_sold=("positive_units", "sum"),
            returned_units=("returned_units", "sum"),
            return_value=("return_value", "sum"),
            return_lines=("is_return", "sum"),
            line_count=("sale_id", "count"),
        )
    )
    audit = audit.loc[audit["units_sold"] >= min_units].copy()
    audit["return_line_rate"] = _safe_divide(audit["return_lines"], audit["line_count"])
    audit["returned_unit_rate"] = _safe_divide(audit["returned_units"], audit["units_sold"])
    audit["risk_label"] = np.select(
        [
            (audit["gross_revenue"] >= audit["gross_revenue"].quantile(0.75))
            & (audit["return_line_rate"] >= 0.08),
            audit["return_line_rate"] >= 0.15,
            audit["returned_unit_rate"] >= 0.10,
        ],
        ["High revenue / high return", "High return rate", "Unit return risk"],
        default="Normal",
    )
    return audit.sort_values(["gross_revenue", "return_line_rate"], ascending=[False, False])


def get_country_metrics(df: pd.DataFrame) -> pd.DataFrame:
    countries = (
        df.groupby("country_name", as_index=False)
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            net_revenue=("line_revenue", "sum"),
            order_count=("invoice_number", "nunique"),
            customer_count=("customer_id", lambda s: s.nunique(dropna=True)),
            units_sold=("positive_units", "sum"),
        )
        .sort_values("gross_revenue", ascending=False)
    )
    countries["aov"] = _safe_divide(countries["gross_revenue"], countries["order_count"])
    total_revenue = countries["gross_revenue"].sum()
    countries["revenue_share"] = _safe_divide(countries["gross_revenue"], total_revenue)
    return countries


def get_data_quality_metrics(df: pd.DataFrame) -> dict[str, object]:
    operational = df.loc[df["is_operational_code"]]
    exceptions = sorted(
        {
            country
            for country in df["country_name"].dropna().unique()
            if country
            in {
                "EIRE",
                "RSA",
                "USA",
                "Unspecified",
                "European Community",
                "Channel Islands",
                "West Indies",
            }
        }
    )
    outlier_rows = int(((df["unit_price"] > 1000) | (df["quantity"].abs() > 1000)).sum())
    return {
        "raw_workbook_rows": RAW_WORKBOOK_ROWS,
        "readme_cleaned_rows": README_CLEANED_ROWS,
        "processed_fact_rows": int(len(df)),
        "null_customer_rows": int(df["customer_id"].isna().sum()),
        "null_customer_rate": float(df["customer_id"].isna().mean()) if len(df) else 0.0,
        "return_rows": int((df["quantity"] < 0).sum()),
        "cancel_invoice_rows": int(df["is_cancel_invoice"].sum()),
        "zero_price_rows": int((df["unit_price"] == 0).sum()),
        "outlier_rows": outlier_rows,
        "country_exceptions": exceptions,
        "operational_rows": int(len(operational)),
        "operational_stock_codes": int(operational["stock_code"].nunique()),
    }


def get_operational_code_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.loc[df["is_operational_code"]]
        .groupby(["stock_code", "product_name"], as_index=False)
        .agg(
            rows=("sale_id", "count"),
            gross_revenue=("gross_revenue", "sum"),
            return_value=("return_value", "sum"),
            units=("quantity", "sum"),
        )
        .sort_values("rows", ascending=False)
        .head(25)
    )


def _customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    known = df.loc[df["customer_id"].notna()].copy()
    if known.empty:
        return pd.DataFrame(
            columns=[
                "customer_id",
                "lifetime_value",
                "order_count",
                "last_order_date",
                "recency_days",
                "recency_bucket",
                "primary_country",
            ]
        )
    latest_date = known["invoice_date"].max()
    summary = (
        known.groupby("customer_id", as_index=False)
        .agg(
            lifetime_value=("gross_revenue", "sum"),
            order_count=("invoice_number", "nunique"),
            last_order_date=("invoice_date", "max"),
            primary_country=("country_name", _mode_or_unknown),
        )
        .sort_values("lifetime_value", ascending=False)
    )
    summary["customer_id"] = summary["customer_id"].astype(int).astype(str)
    summary["recency_days"] = (latest_date - summary["last_order_date"]).dt.days
    summary["recency_bucket"] = pd.cut(
        summary["recency_days"],
        bins=[-1, 30, 90, 180, 365, np.inf],
        labels=["0-30 days", "31-90 days", "91-180 days", "181-365 days", "365+ days"],
    ).astype(str)
    return summary


def _operational_code_mask(df: pd.DataFrame) -> pd.Series:
    stock = df["stock_code"].fillna("").astype(str).str.upper().str.strip()
    desc = df["product_name"].fillna("").astype(str)
    explicit_stock = stock.isin(OPERATIONAL_STOCK_CODES)
    service_like_stock = stock.str.contains(r"^(?:DOT|POST|BANK|AMAZON|DCGS|TEST|ADJUST)", regex=True)
    description_match = desc.str.contains(OPERATIONAL_DESCRIPTION_PATTERN, regex=True, na=False)
    return explicit_stock | service_like_stock | description_match


def _safe_divide(numerator, denominator):
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.divide(numerator, denominator)
    if np.isscalar(result):
        return float(result) if np.isfinite(result) else 0.0
    return pd.Series(result).replace([np.inf, -np.inf], 0).fillna(0).to_numpy()


def _mode_or_unknown(series: pd.Series) -> str:
    modes = series.dropna().mode()
    return str(modes.iloc[0]) if len(modes) else "Unknown"
