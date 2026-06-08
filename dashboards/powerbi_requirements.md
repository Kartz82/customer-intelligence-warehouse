# Power BI Dashboard Requirements
Customer Intelligence Data Warehouse

## Data Source
- PostgreSQL via **DirectQuery** or **Import Mode**
- Connection: `localhost:5433`
- Database: `customer_intelligence_db`

## Data Model Notes
Use the following tables from the warehouse:
- `fact_sales`
- `dim_customer`
- `dim_product`
- `dim_country`

### Measure Definitions
- **Total Revenue** = `SUMX(fact_sales, fact_sales[quantity] * fact_sales[unit_price])` filtered where `is_return = false`
- **Total Orders** = `DISTINCTCOUNT(fact_sales[invoice_number])`
- **Total Customers** = `DISTINCTCOUNT(fact_sales[customer_id])`
- **Return Rate %** = `DIVIDE(CALCULATE(COUNTROWS(fact_sales), fact_sales[is_return] = true), COUNTROWS(fact_sales))`
- **Monthly Revenue** = revenue grouped by month using `invoice_date`
- **Lifetime Value** = total revenue per customer
- **Repeat Purchase Rate %** = percentage of customers with more than 1 distinct order

---

## Page 1 — Executive KPI
### Purpose
Provide a high-level business summary for executives.

### Visuals
- KPI Card: Total Revenue
- KPI Card: Total Orders
- KPI Card: Total Customers
- KPI Card: Return Rate %
- Line Chart: Monthly Revenue Trend
  - Axis: `invoice_date` by month
  - Values: Total Revenue
  - Time span: 25 months
- Bar Chart: Revenue by Country
  - Axis: Country
  - Values: Total Revenue
  - Show top 10 countries

### Filters
- Date range slicer (`invoice_date`)
- Country slicer
- `is_return` toggle

---

## Page 2 — Customer Analysis
### Purpose
Show customer value, loyalty, and retention behavior.

### Visuals
- Table: Top 20 Customers by Lifetime Value
  - Columns: `customer_id`, Lifetime Value, Total Orders
- KPI Card: Repeat Purchase Rate %
- Matrix: Customer Cohort Retention
  - Rows: Cohort month
  - Columns: Months since first order
  - Values: Retention %
- Stacked Bar Chart: New vs Returning Customers per month
  - Axis: Month
  - Values: New Customers, Returning Customers

### Filters
- Date range slicer (`invoice_date`)
- Country slicer
- `is_return` toggle

---

## Page 3 — Product Performance
### Purpose
Identify top-selling products and product-level return risk.

### Visuals
- Bar Chart: Top 20 Products by Revenue
  - Axis: Product
  - Values: Total Revenue
- Bar Chart: Top 20 Products by Quantity Sold
  - Axis: Product
  - Values: Total Quantity
- Scatter Chart: Average Unit Price by Product
  - X-axis: Product
  - Y-axis: Average Unit Price
  - Bubble size: Quantity Sold or Revenue
- Table: Product Return Rate
  - Columns: Product, Return Rate %, Revenue, Quantity
  - Sort descending by Return Rate %

### Filters
- Date range slicer (`invoice_date`)
- Country slicer
- `is_return` toggle

---

## Page 4 — Geographic
### Purpose
Show regional revenue concentration and order distribution.

### Visuals
- Filled Map: Revenue by Country
  - Location: Country
  - Values: Total Revenue
- Table: Order Count by Country
  - Columns: Country, Order Count, Revenue
- Donut Chart: Country Contribution % of Total Revenue
  - Legend: Country
  - Values: Revenue share
  - Show top countries only

### Filters
- Date range slicer (`invoice_date`)
- Country slicer
- `is_return` toggle

---

## Shared Measures
Create the following measures in the semantic model:

```DAX
Total Revenue =
CALCULATE(
    SUMX(fact_sales, fact_sales[quantity] * fact_sales[unit_price]),
    fact_sales[is_return] = FALSE()
)

Total Orders =
DISTINCTCOUNT(fact_sales[invoice_number])

Total Customers =
DISTINCTCOUNT(fact_sales[customer_id])

Return Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(fact_sales), fact_sales[is_return] = TRUE()),
    COUNTROWS(fact_sales)
)

Average Order Value =
DIVIDE([Total Revenue], [Total Orders])

Repeat Purchase Rate % =
DIVIDE(
    COUNTROWS(
        FILTER(
            SUMMARIZE(fact_sales, fact_sales[customer_id], "OrderCount", DISTINCTCOUNT(fact_sales[invoice_number])),
            [OrderCount] > 1
        )
    ),
    DISTINCTCOUNT(fact_sales[customer_id])
)
```

---

## Design Guidelines
- Keep each page focused on one business question.
- Avoid overcrowding a page with too many visuals.
- Use consistent colors for revenue, customers, products, and geography.
- Prefer clear titles and short labels.
- Use tooltips for extra detail instead of adding more charts.

---

## Expected Outcome
This dashboard should help users answer:
- How is the business performing overall?
- Which customers are most valuable?
- Which products are driving revenue or returns?
- Which countries are contributing most to growth?

---

## Notes
- Use `Import Mode` if performance is acceptable and data refresh is not required in real time.
- Use `DirectQuery` only if live querying is required.
- Ensure `invoice_date` is properly typed as a datetime field in PostgreSQL.
- Validate that `is_return` is a boolean field in the warehouse.