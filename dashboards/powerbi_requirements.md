# Power BI Dashboard Requirements

## Data Source
PostgreSQL via DirectQuery or Import Mode
Connection: localhost:5433 | DB: customer_intelligence_db

## Page 1 — Executive KPI
- Total Revenue (SUM of quantity * unit_price, is_return = false)
- Total Orders (COUNT DISTINCT invoice_number)
- Total Customers (COUNT DISTINCT customer_id)
- Return Rate % (COUNT where is_return = true / total)
- Monthly Revenue Trend (line chart, 25 months)
- Revenue by Country (bar chart, top 10)

## Page 2 — Customer Analysis
- Top 20 Customers by Lifetime Value (table)
- Repeat Purchase Rate KPI card
- Customer Cohort Retention (matrix: cohort month vs months since first order)
- New vs Returning Customers per month (stacked bar)

## Page 3 — Product Performance
- Top 20 Products by Revenue (bar chart)
- Top 20 Products by Quantity Sold (bar chart)
- Average Unit Price by Product (scatter)
- Product Return Rate (table, sorted desc)

## Page 4 — Geographic
- Revenue by Country (filled map)
- Order Count by Country (table)
- Country contribution % of total revenue (donut chart)

## Filters (all pages)
- Date range slicer (invoice_date)
- Country slicer
- is_return toggle