"""Live streaming trust dashboard (standalone).

Reads the streaming layer straight from PostgreSQL and shows the BI-readiness
scorecard, accept/quarantine mix, AI-clean decision methods, and a live feed of
what the gate abstained on. Auto-refreshes.

Separate Dash app (port 8051) so the main batch dashboard stays untouched.

    python -m streaming.dashboard      # http://localhost:8051
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import psycopg2
from dash import Dash, Input, Output, dash_table, dcc, html

from streaming.settings import load_settings

# --- palette shared with the main dashboard for visual consistency ---
BACKGROUND = "#050B14"
PANEL = "#0F172A"
CARD = "#111827"
BORDER = "#243244"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
BLUE = "#38BDF8"
TEAL = "#2DD4BF"
GREEN = "#22C55E"
AMBER = "#F59E0B"
ROSE = "#F43F5E"

_CFG = load_settings()


def _q(sql: str) -> pd.DataFrame:
    with psycopg2.connect(_CFG.db_url) as conn:
        return pd.read_sql(sql, conn)


def load_scorecard() -> dict:
    try:
        df = _q("SELECT * FROM analytics_streaming.mart_bi_readiness")
        return df.iloc[0].to_dict() if not df.empty else {}
    except Exception as exc:
        print(f"[dashboard] scorecard unavailable: {exc}")
        return {}


def load_quarantine_reasons() -> pd.DataFrame:
    return _q("""SELECT reason, count(*) AS n
                 FROM orders_quarantine GROUP BY reason ORDER BY n DESC""")


def load_methods() -> pd.DataFrame:
    return _q("""SELECT method, count(*) AS n
                 FROM orders_clean_audit GROUP BY method ORDER BY n DESC""")


def load_recent_quarantine(limit: int = 15) -> pd.DataFrame:
    return _q(f"""SELECT quarantined_at::timestamp(0) AS at, reason, field,
                         raw_value AS "raw value"
                  FROM orders_quarantine ORDER BY quarantined_at DESC LIMIT {limit}""")


# ------------------------------------------------------------------ ui ----

def score_color(score: float) -> str:
    if score >= 85:
        return GREEN
    if score >= 70:
        return AMBER
    return ROSE


def kpi_card(label: str, value: str, color: str = TEXT) -> html.Div:
    return html.Div(
        style={"background": CARD, "border": f"1px solid {BORDER}",
               "borderRadius": "12px", "padding": "18px 20px", "flex": "1",
               "minWidth": "160px"},
        children=[
            html.Div(label, style={"color": MUTED, "fontSize": "13px",
                                   "textTransform": "uppercase", "letterSpacing": "0.5px"}),
            html.Div(value, style={"color": color, "fontSize": "30px",
                                   "fontWeight": 700, "marginTop": "6px"}),
        ],
    )


app = Dash(__name__)
app.title = "Streaming Trust Monitor"

app.layout = html.Div(
    style={"background": BACKGROUND, "minHeight": "100vh", "padding": "28px 36px",
           "fontFamily": "Inter, system-ui, sans-serif", "color": TEXT},
    children=[
        html.Div([
            html.H1("Streaming BI-Readiness Monitor",
                    style={"margin": 0, "fontSize": "26px"}),
            html.P("Live order stream → AI-clean gate (abstains when unsure) → governed warehouse",
                   style={"color": MUTED, "marginTop": "6px"}),
        ]),
        dcc.Interval(id="tick", interval=5000, n_intervals=0),
        html.Div(id="kpis", style={"display": "flex", "gap": "16px",
                                   "flexWrap": "wrap", "marginTop": "18px"}),
        html.Div(style={"display": "flex", "gap": "16px", "marginTop": "20px",
                        "flexWrap": "wrap"},
                 children=[
                     html.Div(dcc.Graph(id="reasons"), style={"flex": "1", "minWidth": "360px"}),
                     html.Div(dcc.Graph(id="methods"), style={"flex": "1", "minWidth": "360px"}),
                 ]),
        html.H3("Abstention feed — what the gate refused to guess",
                style={"marginTop": "24px", "fontSize": "16px"}),
        html.Div(id="feed"),
    ],
)


def _fig(fig: go.Figure) -> go.Figure:
    fig.update_layout(paper_bgcolor=PANEL, plot_bgcolor=PANEL, font_color=TEXT,
                      margin=dict(l=20, r=20, t=48, b=20), height=320)
    return fig


@app.callback(
    Output("kpis", "children"), Output("reasons", "figure"),
    Output("methods", "figure"), Output("feed", "children"),
    Input("tick", "n_intervals"),
)
def refresh(_):
    s = load_scorecard()
    score = float(s.get("bi_readiness_score", 0) or 0)
    reconciles = bool(s.get("reconciles", False))
    kpis = [
        kpi_card("BI-Readiness", f"{score:.0f}", score_color(score)),
        kpi_card("Accept rate", f"{float(s.get('accept_score', 0) or 0):.0f}%", BLUE),
        kpi_card("Landed", f"{int(s.get('n_landed', 0) or 0):,}"),
        kpi_card("Promoted", f"{int(s.get('n_promoted', 0) or 0):,}", GREEN),
        kpi_card("Quarantined", f"{int(s.get('n_quarantined', 0) or 0):,}", ROSE),
        kpi_card("LLM assists", f"{int(s.get('llm_interventions', 0) or 0):,}", TEAL),
        kpi_card("Stream revenue", f"${float(s.get('stream_revenue', 0) or 0):,.0f}"),
        kpi_card("Reconciles", "yes" if reconciles else "NO", GREEN if reconciles else ROSE),
    ]

    reasons = load_quarantine_reasons()
    rfig = _fig(go.Figure(go.Bar(
        x=reasons["n"], y=reasons["reason"], orientation="h", marker_color=ROSE)))
    rfig.update_layout(title="Why events were quarantined")

    methods = load_methods()
    color_map = {"rule": BLUE, "llm": TEAL, "passthrough": MUTED}
    mfig = _fig(go.Figure(go.Pie(
        labels=methods["method"], values=methods["n"], hole=0.55,
        marker_colors=[color_map.get(m, MUTED) for m in methods["method"]])))
    mfig.update_layout(title="AI-clean decisions (rule vs LLM)")

    feed_df = load_recent_quarantine()
    feed = dash_table.DataTable(
        data=feed_df.astype(str).to_dict("records"),
        columns=[{"name": c, "id": c} for c in feed_df.columns],
        style_header={"backgroundColor": PANEL, "color": TEXT, "fontWeight": "bold",
                      "border": f"1px solid {BORDER}"},
        style_cell={"backgroundColor": CARD, "color": TEXT, "border": f"1px solid {BORDER}",
                    "fontSize": "13px", "padding": "8px", "textAlign": "left"},
        page_size=15,
    )
    return kpis, rfig, mfig, feed


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8051, debug=False)
