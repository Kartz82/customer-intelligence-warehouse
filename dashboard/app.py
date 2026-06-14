from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from dash import Dash, Input, Output, dash_table, dcc, html
import plotly.express as px
import plotly.graph_objects as go


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard_data import (  # noqa: E402
    filter_fact,
    get_country_metrics,
    get_customer_metrics,
    get_customer_summary,
    get_data_quality_metrics,
    get_executive_metrics,
    get_monthly_revenue,
    get_operational_code_summary,
    get_product_metrics,
    get_product_return_audit,
    get_top_customers,
    load_fact_sales,
)


BACKGROUND = "#050B14"
PANEL = "#0F172A"
CARD = "#111827"
BORDER = "#243244"
TEXT = "#F8FAFC"
SECONDARY_TEXT = "#CBD5E1"
MUTED = "#94A3B8"

BLUE = "#38BDF8"
TEAL = "#2DD4BF"
GREEN = "#22C55E"
AMBER = "#F59E0B"
ORANGE = "#F97316"
ROSE = "#F43F5E"
RED = "#EF4444"
GRAY = "#64748B"


FACT_DF = load_fact_sales()
MIN_DATE = FACT_DF["invoice_date"].min().date()
MAX_DATE = FACT_DF["invoice_date"].max().date()
COUNTRIES = sorted(FACT_DF["country_name"].dropna().unique())

app = Dash(__name__, title="Customer Intelligence Dashboard", suppress_callback_exceptions=True)
server = app.server


def kpi_card(label: str, value: str, accent: str = BLUE, helper: str | None = None) -> html.Div:
    return html.Div(
        className="kpi-card",
        style={"borderTopColor": accent},
        children=[
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
            html.Div(helper or "", className="kpi-helper"),
        ],
    )


def chart_card(title: str, figure: go.Figure, subtitle: str | None = None) -> html.Div:
    return html.Div(
        className="chart-card",
        children=[
            html.Div(
                className="chart-header",
                children=[
                    html.H3(title),
                    html.P(subtitle or ""),
                ],
            ),
            dcc.Graph(figure=figure, config={"displayModeBar": False}, className="chart"),
        ],
    )


def table_card(title: str, table: dash_table.DataTable, subtitle: str | None = None) -> html.Div:
    return html.Div(
        className="chart-card",
        children=[
            html.Div(
                className="chart-header",
                children=[
                    html.H3(title),
                    html.P(subtitle or ""),
                ],
            ),
            table,
        ],
    )


def empty_figure(message: str = "No data for selected filters") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, showarrow=False, font={"color": SECONDARY_TEXT, "size": 16})
    return style_figure(fig)


def style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font={"color": TEXT, "family": "Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif"},
        margin={"l": 40, "r": 24, "t": 24, "b": 40},
        hoverlabel={"bgcolor": CARD, "bordercolor": BORDER, "font_color": TEXT},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER, title_font={"color": SECONDARY_TEXT})
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER, title_font={"color": SECONDARY_TEXT})
    return fig


def money(value: float) -> str:
    return f"£{value:,.0f}"


def count(value: float) -> str:
    return f"{value:,.0f}"


def pct(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def compact_money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"£{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"£{value / 1_000:.1f}K"
    return money(value)


def make_table(df: pd.DataFrame, columns: list[dict], page_size: int = 10, risk_column: str | None = None):
    style_data_conditional = []
    if risk_column:
        style_data_conditional.extend(
            [
                {
                    "if": {"filter_query": f'{{{risk_column}}} contains "High"', "column_id": risk_column},
                    "backgroundColor": "rgba(244, 63, 94, 0.22)",
                    "color": TEXT,
                },
                {
                    "if": {"filter_query": f'{{{risk_column}}} contains "Unit"', "column_id": risk_column},
                    "backgroundColor": "rgba(249, 115, 22, 0.18)",
                    "color": TEXT,
                },
            ]
        )
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=columns,
        page_size=page_size,
        sort_action="native",
        filter_action="native",
        style_as_list_view=True,
        style_table={"overflowX": "auto"},
        style_cell={
            "backgroundColor": CARD,
            "color": SECONDARY_TEXT,
            "border": f"1px solid {BORDER}",
            "fontFamily": "Inter, system-ui, sans-serif",
            "fontSize": "13px",
            "padding": "10px",
            "textAlign": "left",
            "minWidth": "110px",
        },
        style_header={
            "backgroundColor": PANEL,
            "color": TEXT,
            "fontWeight": "700",
            "border": f"1px solid {BORDER}",
        },
        style_data_conditional=style_data_conditional,
    )


app.layout = html.Div(
    className="app-shell",
    children=[
        html.Div(
            className="page-header",
            children=[
                html.Div(
                    [
                        html.P("Customer Intelligence Data Warehouse", className="eyebrow"),
                        html.H1("Executive Analytics Dashboard"),
                        html.P(
                            "CSV-mode Plotly Dash rebuild using the processed fact export. "
                            "Totals reflect the available processed extract.",
                            className="subtitle",
                        ),
                    ]
                ),
                html.Div(
                    className="source-note",
                    children=[
                        html.Strong("Data caveat"),
                        html.Span(
                            "Dashboard currently uses processed fact export. Raw workbook contains more rows; "
                            "totals reflect the available processed extract."
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className="filters-panel",
            children=[
                html.Div(
                    className="filter-item date-filter",
                    children=[
                        html.Label("Date Range"),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=MIN_DATE,
                            max_date_allowed=MAX_DATE,
                            start_date=MIN_DATE,
                            end_date=MAX_DATE,
                            display_format="YYYY-MM-DD",
                        ),
                    ],
                ),
                html.Div(
                    className="filter-item country-filter",
                    children=[
                        html.Label("Countries"),
                        dcc.Dropdown(
                            id="country-filter",
                            options=[{"label": country, "value": country} for country in COUNTRIES],
                            multi=True,
                            placeholder="All countries",
                        ),
                    ],
                ),
                html.Div(
                    className="filter-item toggle-filter",
                    children=[
                        html.Label("Product Analytics"),
                        dcc.Checklist(
                            id="include-operational",
                            options=[
                                {
                                    "label": "Include operational/non-product codes",
                                    "value": "include",
                                }
                            ],
                            value=[],
                            inputClassName="check-input",
                            labelClassName="check-label",
                        ),
                    ],
                ),
                html.Div(
                    className="filter-item toggle-filter",
                    children=[
                        html.Label("Revenue View"),
                        dcc.RadioItems(
                            id="revenue-mode",
                            options=[
                                {"label": "Gross", "value": "gross"},
                                {"label": "Net", "value": "net"},
                            ],
                            value="gross",
                            inline=True,
                            className="radio-group",
                        ),
                    ],
                ),
            ],
        ),
        dcc.Tabs(
            id="tabs",
            value="executive",
            className="tabs",
            children=[
                dcc.Tab(label="Executive Overview", value="executive", className="tab", selected_className="tab-selected"),
                dcc.Tab(label="Customer Intelligence", value="customers", className="tab", selected_className="tab-selected"),
                dcc.Tab(label="Product & Return Audit", value="products", className="tab", selected_className="tab-selected"),
                dcc.Tab(label="Geographic Performance", value="geography", className="tab", selected_className="tab-selected"),
                dcc.Tab(label="Data Quality / Warehouse Health", value="quality", className="tab", selected_className="tab-selected"),
            ],
        ),
        html.Div(id="tab-content", className="tab-content"),
    ],
)


@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("country-filter", "value"),
    Input("include-operational", "value"),
    Input("revenue-mode", "value"),
)
def render_tab(tab, start_date, end_date, countries, include_operational_values, revenue_mode):
    include_operational = "include" in (include_operational_values or [])
    filtered = filter_fact(
        FACT_DF,
        start_date=start_date,
        end_date=end_date,
        countries=countries,
    )
    if tab == "executive":
        return render_executive(filtered, include_operational)
    if tab == "customers":
        return render_customers(filtered)
    if tab == "products":
        return render_products(filtered, revenue_mode, include_operational)
    if tab == "geography":
        return render_geography(filtered)
    return render_quality(filtered)


def render_executive(df: pd.DataFrame, include_operational: bool):
    metrics = get_executive_metrics(df)
    monthly = get_monthly_revenue(df)
    countries = get_country_metrics(df)
    customers = get_customer_summary(df)
    products = get_product_return_audit(df, include_operational=include_operational)

    monthly_fig = empty_figure() if monthly.empty else go.Figure()
    if not monthly.empty:
        monthly_fig.add_trace(
            go.Scatter(
                x=monthly["month"],
                y=monthly["gross_revenue"],
                mode="lines+markers",
                name="Gross Revenue",
                line={"color": AMBER, "width": 3},
                hovertemplate="%{x|%b %Y}<br>Gross: £%{y:,.0f}<extra></extra>",
            )
        )
        monthly_fig.add_trace(
            go.Scatter(
                x=monthly["month"],
                y=monthly["net_revenue"],
                mode="lines+markers",
                name="Net Revenue",
                line={"color": TEAL, "width": 3},
                hovertemplate="%{x|%b %Y}<br>Net: £%{y:,.0f}<extra></extra>",
            )
        )
        monthly_fig.update_yaxes(title="Revenue", tickprefix="£", separatethousands=True)
        monthly_fig.update_xaxes(title="")
        monthly_fig = style_figure(monthly_fig)

    top_countries = countries.head(10).sort_values("gross_revenue")
    country_fig = empty_figure() if top_countries.empty else px.bar(
        top_countries,
        x="gross_revenue",
        y="country_name",
        orientation="h",
        color="gross_revenue",
        color_continuous_scale=[[0, BLUE], [1, AMBER]],
        labels={"gross_revenue": "Gross Revenue", "country_name": ""},
    )
    if not top_countries.empty:
        country_fig.update_layout(coloraxis_showscale=False)
        country_fig.update_xaxes(title="Gross Revenue", tickprefix="£", separatethousands=True)
        country_fig = style_figure(country_fig)

    total_revenue = metrics["gross_revenue"]
    top_customer_share = (
        customers["lifetime_value"].iloc[0] / total_revenue if total_revenue and len(customers) else 0.0
    )
    top10_customer_share = (
        customers["lifetime_value"].head(10).sum() / total_revenue if total_revenue and len(customers) else 0.0
    )
    uk_revenue = float(countries.loc[countries["country_name"] == "United Kingdom", "gross_revenue"].sum())
    uk_share = uk_revenue / total_revenue if total_revenue else 0.0
    top10_product_share = (
        products["gross_revenue"].head(10).sum() / total_revenue if total_revenue and len(products) else 0.0
    )

    return html.Div(
        [
            html.Div(
                className="kpi-grid eight",
                children=[
                    kpi_card("Gross Revenue", money(metrics["gross_revenue"]), AMBER),
                    kpi_card("Net Revenue", money(metrics["net_revenue"]), TEAL),
                    kpi_card("Total Units Sold", count(metrics["total_units_sold"]), BLUE),
                    kpi_card("Active Customers", count(metrics["active_customers"]), GREEN),
                    kpi_card("Total Transactions", count(metrics["total_transactions"]), BLUE),
                    kpi_card("Average Order Value", money(metrics["average_order_value"]), AMBER),
                    kpi_card("Repeat Purchase Rate", pct(metrics["repeat_purchase_rate"]), GREEN),
                    kpi_card("Return Value", money(metrics["return_value"]), ROSE),
                ],
            ),
            html.Div(
                className="two-column",
                children=[
                    chart_card("Monthly Revenue Trend", monthly_fig, "Gross positive revenue with net revenue after returns."),
                    chart_card("Revenue by Country", country_fig, "Top 10 countries by gross revenue."),
                ],
            ),
            html.Div(
                className="kpi-grid four",
                children=[
                    kpi_card("Top Customer Share", pct(top_customer_share), AMBER, "Largest customer as share of gross revenue"),
                    kpi_card("Top 10 Customer Share", pct(top10_customer_share), AMBER),
                    kpi_card("Top 10 Product Share", pct(top10_product_share), BLUE),
                    kpi_card("UK Revenue Share", pct(uk_share), TEAL, compact_money(uk_revenue)),
                ],
            ),
        ]
    )


def render_customers(df: pd.DataFrame):
    metrics = get_customer_metrics(df)
    customers = get_customer_summary(df)
    top_customers = get_top_customers(df, 15).sort_values("lifetime_value")

    top_fig = empty_figure() if top_customers.empty else px.bar(
        top_customers,
        x="lifetime_value",
        y="customer_id",
        orientation="h",
        labels={"lifetime_value": "Lifetime Value", "customer_id": "Customer ID"},
        color_discrete_sequence=[AMBER],
    )
    if not top_customers.empty:
        top_fig.update_xaxes(tickprefix="£", separatethousands=True)
        top_fig = style_figure(top_fig)

    scatter = customers.copy()
    scatter_fig = empty_figure() if scatter.empty else px.scatter(
        scatter,
        x="order_count",
        y="lifetime_value",
        color="recency_bucket",
        hover_data=["customer_id", "primary_country", "recency_days"],
        labels={
            "order_count": "Order Frequency",
            "lifetime_value": "Lifetime Value",
            "recency_bucket": "Recency",
        },
        color_discrete_sequence=[GREEN, TEAL, BLUE, ORANGE, ROSE],
    )
    if not scatter.empty:
        scatter_fig.update_yaxes(tickprefix="£", separatethousands=True)
        scatter_fig = style_figure(scatter_fig)

    hist_fig = empty_figure() if customers.empty else px.histogram(
        customers,
        x="order_count",
        nbins=40,
        labels={"order_count": "Number of Orders", "count": "Customer Count"},
        color_discrete_sequence=[TEAL],
    )
    if not customers.empty:
        hist_fig.update_yaxes(title="Customer Count")
        hist_fig = style_figure(hist_fig)

    table_df = (
        customers.head(50)
        .assign(
            lifetime_value=lambda d: d["lifetime_value"].map(lambda v: f"£{v:,.0f}"),
            last_order_date=lambda d: d["last_order_date"].dt.strftime("%Y-%m-%d"),
        )
        [["customer_id", "lifetime_value", "order_count", "recency_days", "recency_bucket", "primary_country", "last_order_date"]]
    )
    table = make_table(
        table_df,
        [
            {"name": "Customer ID", "id": "customer_id"},
            {"name": "Lifetime Value", "id": "lifetime_value"},
            {"name": "Orders", "id": "order_count", "type": "numeric"},
            {"name": "Recency Days", "id": "recency_days", "type": "numeric"},
            {"name": "Recency Bucket", "id": "recency_bucket"},
            {"name": "Primary Country", "id": "primary_country"},
            {"name": "Last Order", "id": "last_order_date"},
        ],
    )

    return html.Div(
        [
            html.Div(
                className="kpi-grid five",
                children=[
                    kpi_card("Known Customers", count(metrics["known_customers"]), GREEN),
                    kpi_card("Guest / Null Customer Rows", pct(metrics["guest_row_rate"]), ROSE),
                    kpi_card("Repeat Purchase Rate", pct(metrics["repeat_purchase_rate"]), GREEN),
                    kpi_card("Median LTV", money(metrics["median_ltv"]), AMBER),
                    kpi_card("Average Order Frequency", f"{metrics['avg_order_frequency']:.1f}", BLUE),
                ],
            ),
            html.Div(
                className="two-column",
                children=[
                    chart_card("Top Customers by LTV", top_fig, "Top 15 known customers by positive revenue."),
                    chart_card("LTV vs Order Frequency", scatter_fig, "Color indicates recency bucket from the latest order date."),
                ],
            ),
            html.Div(
                className="two-column narrow-right",
                children=[
                    chart_card("Order Frequency Distribution", hist_fig, "Known customers only."),
                    table_card("Top Customer Table", table, "Sortable and filterable customer-level metrics."),
                ],
            ),
        ]
    )


def render_products(df: pd.DataFrame, revenue_mode: str, include_operational: bool):
    metrics = get_product_metrics(df, include_operational=include_operational)
    audit = get_product_return_audit(df, include_operational=include_operational)
    revenue_col = "net_revenue" if revenue_mode == "net" else "gross_revenue"
    revenue_label = "Net Revenue" if revenue_mode == "net" else "Gross Revenue"

    top_products = audit.sort_values(revenue_col, ascending=False).head(15).sort_values(revenue_col)
    top_fig = empty_figure() if top_products.empty else px.bar(
        top_products,
        x=revenue_col,
        y="product_name",
        orientation="h",
        labels={revenue_col: revenue_label, "product_name": ""},
        color_discrete_sequence=[AMBER],
        hover_data=["stock_code", "units_sold", "returned_units"],
    )
    if not top_products.empty:
        top_fig.update_xaxes(tickprefix="£", separatethousands=True)
        top_fig = style_figure(top_fig)

    scatter_df = audit.loc[audit["gross_revenue"] > 0].copy()
    if not scatter_df.empty:
        unit_size_cap = float(scatter_df["units_sold"].quantile(0.95) or 1)
        scatter_df["bubble_units"] = scatter_df["units_sold"].clip(lower=1, upper=unit_size_cap).astype(float)
    scatter_fig = empty_figure() if scatter_df.empty else px.scatter(
        scatter_df,
        x="gross_revenue",
        y="return_line_rate",
        size="bubble_units",
        color="risk_label",
        hover_data=["stock_code", "product_name", "units_sold", "returned_units", "returned_unit_rate"],
        labels={
            "gross_revenue": "Gross Revenue",
            "return_line_rate": "Return Line Rate",
            "risk_label": "Risk Level",
        },
        color_discrete_map={
            "High revenue / high return": ROSE,
            "High return rate": RED,
            "Unit return risk": ORANGE,
            "Normal": BLUE,
        },
    )
    if not scatter_df.empty:
        high_rev_threshold = scatter_df["gross_revenue"].quantile(0.75)
        return_threshold = 0.08
        scatter_fig.add_vline(x=high_rev_threshold, line_color=GRAY, line_dash="dash")
        scatter_fig.add_hline(y=return_threshold, line_color=ROSE, line_dash="dash")
        scatter_fig.update_xaxes(tickprefix="£", separatethousands=True)
        scatter_fig.update_yaxes(tickformat=".1%")
        scatter_fig = style_figure(scatter_fig)

    matrix_fig = empty_figure() if scatter_df.empty else px.scatter(
        scatter_df,
        x="gross_revenue",
        y="returned_unit_rate",
        size="bubble_units",
        color="risk_label",
        hover_data=["stock_code", "product_name", "return_line_rate", "returned_units"],
        labels={
            "gross_revenue": "Gross Revenue",
            "returned_unit_rate": "Returned Unit Rate",
            "risk_label": "Risk Level",
        },
        color_discrete_map={
            "High revenue / high return": ROSE,
            "High return rate": RED,
            "Unit return risk": ORANGE,
            "Normal": TEAL,
        },
    )
    if not scatter_df.empty:
        matrix_fig.add_vline(x=scatter_df["gross_revenue"].quantile(0.75), line_color=GRAY, line_dash="dash")
        matrix_fig.add_hline(y=0.10, line_color=ORANGE, line_dash="dash")
        matrix_fig.update_xaxes(tickprefix="£", separatethousands=True)
        matrix_fig.update_yaxes(tickformat=".1%")
        matrix_fig = style_figure(matrix_fig)

    table_df = audit.head(75).assign(
        gross_revenue=lambda d: d["gross_revenue"].map(lambda v: f"£{v:,.0f}"),
        units_sold=lambda d: d["units_sold"].map(lambda v: f"{v:,.0f}"),
        returned_units=lambda d: d["returned_units"].map(lambda v: f"{v:,.0f}"),
        return_line_rate=lambda d: d["return_line_rate"].map(lambda v: f"{v * 100:.1f}%"),
        returned_unit_rate=lambda d: d["returned_unit_rate"].map(lambda v: f"{v * 100:.1f}%"),
    )[
        [
            "product_name",
            "stock_code",
            "gross_revenue",
            "units_sold",
            "returned_units",
            "return_line_rate",
            "returned_unit_rate",
            "risk_label",
        ]
    ]
    table = make_table(
        table_df,
        [
            {"name": "Product", "id": "product_name"},
            {"name": "Stock Code", "id": "stock_code"},
            {"name": "Gross Revenue", "id": "gross_revenue"},
            {"name": "Units Sold", "id": "units_sold"},
            {"name": "Returned Units", "id": "returned_units"},
            {"name": "Return Line Rate", "id": "return_line_rate"},
            {"name": "Returned Unit Rate", "id": "returned_unit_rate"},
            {"name": "Risk Label", "id": "risk_label"},
        ],
        page_size=12,
        risk_column="risk_label",
    )

    return html.Div(
        [
            html.Div(
                className="kpi-grid six",
                children=[
                    kpi_card("Product Count", count(metrics["product_count"]), BLUE),
                    kpi_card("Units Sold", count(metrics["units_sold"]), GREEN),
                    kpi_card("Returned Units", count(metrics["returned_units"]), ROSE),
                    kpi_card("Return Value", money(metrics["return_value"]), ROSE),
                    kpi_card("Return Line Rate", pct(metrics["return_line_rate"]), ORANGE),
                    kpi_card("Returned Unit Rate", pct(metrics["returned_unit_rate"]), ORANGE),
                ],
            ),
            html.Div(
                className="two-column",
                children=[
                    chart_card(
                        f"Top Products by {revenue_label}",
                        top_fig,
                        "Operational/non-product codes excluded by default unless enabled in filters.",
                    ),
                    chart_card("Revenue vs Return Rate", scatter_fig, "Threshold lines mark high revenue and elevated return-line risk."),
                ],
            ),
            html.Div(
                className="two-column narrow-left",
                children=[
                    chart_card("Product Return-Risk Matrix", matrix_fig, "Returned-unit risk against revenue."),
                    table_card(
                        "Product Return Audit Table",
                        table,
                        "Operational codes are excluded defensively by default using stock code and description patterns.",
                    ),
                ],
            ),
        ]
    )


def render_geography(df: pd.DataFrame):
    countries = get_country_metrics(df)
    total_revenue = float(countries["gross_revenue"].sum()) if len(countries) else 0.0
    top_country = countries.iloc[0] if len(countries) else None
    uk_revenue = float(countries.loc[countries["country_name"] == "United Kingdom", "gross_revenue"].sum())
    international = countries.loc[countries["country_name"] != "United Kingdom"]

    top15 = countries.head(15).sort_values("gross_revenue")
    bar_fig = empty_figure() if top15.empty else px.bar(
        top15,
        x="gross_revenue",
        y="country_name",
        orientation="h",
        labels={"gross_revenue": "Gross Revenue", "country_name": ""},
        color="gross_revenue",
        color_continuous_scale=[[0, TEAL], [1, AMBER]],
    )
    if not top15.empty:
        bar_fig.update_layout(coloraxis_showscale=False)
        bar_fig.update_xaxes(tickprefix="£", separatethousands=True)
        bar_fig = style_figure(bar_fig)

    if not countries.empty:
        customer_size_cap = float(countries["customer_count"].quantile(0.95) or 1)
        countries = countries.assign(
            bubble_customers=pd.to_numeric(countries["customer_count"], errors="coerce")
            .fillna(1)
            .astype(float)
            .clip(lower=1, upper=customer_size_cap)
        )
    scatter_fig = empty_figure() if countries.empty else px.scatter(
        countries,
        x="order_count",
        y="gross_revenue",
        size="bubble_customers",
        color="aov",
        color_continuous_scale=[[0, BLUE], [0.5, TEAL], [1, AMBER]],
        hover_data=["country_name", "customer_count", "aov", "revenue_share"],
        labels={"order_count": "Order Count", "gross_revenue": "Gross Revenue", "aov": "AOV"},
    )
    if not countries.empty:
        scatter_fig.update_yaxes(tickprefix="£", separatethousands=True)
        scatter_fig.update_layout(coloraxis_colorbar={"title": "AOV", "tickprefix": "£"})
        scatter_fig = style_figure(scatter_fig)

    aov_df = countries.sort_values("order_count", ascending=False).head(15).sort_values("aov")
    aov_fig = empty_figure() if aov_df.empty else px.bar(
        aov_df,
        x="aov",
        y="country_name",
        orientation="h",
        labels={"aov": "Average Order Value", "country_name": ""},
        color_discrete_sequence=[GREEN],
    )
    if not aov_df.empty:
        aov_fig.update_xaxes(tickprefix="£", separatethousands=True)
        aov_fig = style_figure(aov_fig)

    return html.Div(
        [
            html.Div(
                className="kpi-grid five",
                children=[
                    kpi_card("Country Count", count(len(countries)), BLUE),
                    kpi_card("Top Country", str(top_country["country_name"]) if top_country is not None else "N/A", AMBER),
                    kpi_card("UK Revenue Share", pct(uk_revenue / total_revenue if total_revenue else 0), TEAL),
                    kpi_card("International Revenue", money(float(international["gross_revenue"].sum())), GREEN),
                    kpi_card("International Order Count", count(float(international["order_count"].sum())), BLUE),
                ],
            ),
            html.Div(
                className="two-column",
                children=[
                    chart_card("Country Revenue Bar", bar_fig, "Top 15 countries by gross revenue."),
                    chart_card("Country Revenue vs Order Volume", scatter_fig, "Bubble size reflects known customer count."),
                ],
            ),
            html.Div(
                className="one-column",
                children=[
                    chart_card("AOV by Country", aov_fig, "Top countries by order count, ranked by AOV."),
                ],
            ),
        ]
    )


def render_quality(df: pd.DataFrame):
    quality = get_data_quality_metrics(df)
    operational = get_operational_code_summary(df).assign(
        gross_revenue=lambda d: d["gross_revenue"].map(lambda v: f"£{v:,.0f}"),
        return_value=lambda d: d["return_value"].map(lambda v: f"£{v:,.0f}"),
        units=lambda d: d["units"].map(lambda v: f"{v:,.0f}"),
    )
    country_exceptions = pd.DataFrame({"country_name": quality["country_exceptions"]})
    if country_exceptions.empty:
        country_exceptions = pd.DataFrame({"country_name": ["No known mapping exceptions in selected filters"]})

    lineage = pd.DataFrame(
        {
            "stage": ["Raw workbook rows", "README cleaned rows", "Processed fact export rows"],
            "rows": [
                quality["raw_workbook_rows"],
                quality["readme_cleaned_rows"],
                quality["processed_fact_rows"],
            ],
        }
    )
    lineage_fig = px.bar(
        lineage,
        x="stage",
        y="rows",
        color="stage",
        color_discrete_sequence=[GRAY, BLUE, AMBER],
        labels={"stage": "", "rows": "Rows"},
    )
    lineage_fig.update_yaxes(separatethousands=True)
    lineage_fig.update_layout(showlegend=False)
    lineage_fig = style_figure(lineage_fig)

    operational_table = make_table(
        operational,
        [
            {"name": "Stock Code", "id": "stock_code"},
            {"name": "Description", "id": "product_name"},
            {"name": "Rows", "id": "rows"},
            {"name": "Gross Revenue", "id": "gross_revenue"},
            {"name": "Return Value", "id": "return_value"},
            {"name": "Units", "id": "units"},
        ],
        page_size=8,
    )
    exceptions_table = make_table(
        country_exceptions,
        [{"name": "Country Mapping Exception", "id": "country_name"}],
        page_size=8,
    )

    return html.Div(
        [
            html.Div(
                className="kpi-grid seven",
                children=[
                    kpi_card("Raw Workbook Rows", count(quality["raw_workbook_rows"]), GRAY),
                    kpi_card("Processed Fact Rows", count(quality["processed_fact_rows"]), AMBER),
                    kpi_card("Null Customer Rows", count(quality["null_customer_rows"]), ROSE),
                    kpi_card("Null Customer Row %", pct(quality["null_customer_rate"]), ROSE),
                    kpi_card("Return Rows", count(quality["return_rows"]), ORANGE),
                    kpi_card("Zero-Price Rows", count(quality["zero_price_rows"]), ORANGE),
                    kpi_card("Outlier Rows", count(quality["outlier_rows"]), RED),
                ],
            ),
            html.Div(
                className="quality-note",
                children=[
                    html.Strong("Return logic note: "),
                    html.Span(
                        "This dashboard treats negative-quantity rows as returns. Cancelled invoice prefixes are also tracked "
                        f"for audit context; selected data contains {quality['cancel_invoice_rows']:,} invoice rows beginning with C."
                    ),
                ],
            ),
            html.Div(
                className="two-column",
                children=[
                    chart_card("Raw-to-Processed Lineage Summary", lineage_fig, "The dashboard reads the processed fact export, not the raw workbook."),
                    table_card("Country Mapping Exceptions", exceptions_table, "Map visuals were intentionally skipped until country normalization is explicit."),
                ],
            ),
            html.Div(
                className="one-column",
                children=[
                    table_card("Operational Stock Code Summary", operational_table, "Rows excluded from product analytics by default."),
                ],
            ),
        ]
    )


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
