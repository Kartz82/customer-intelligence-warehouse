# DAX Measures

Assumptions:

- CSV table names in Power BI match the dbt mart names.
- Column names are imported exactly as exported from dbt.
- `mart_executive_kpis` and `mart_repeat_purchase_metrics` are one-row summary tables.
- `mart_sales_monthly`, `mart_country_revenue`, and `mart_customer_lifetime_value` are pre-aggregated reporting tables.

## Executive KPI Measures

```DAX
Total Revenue =
SUM ( mart_executive_kpis[total_revenue] )
```

```DAX
Total Customers =
SUM ( mart_executive_kpis[total_customers] )
```

```DAX
Total Invoices =
SUM ( mart_executive_kpis[total_invoices] )
```

```DAX
Average Order Value =
DIVIDE ( [Total Revenue], [Total Invoices] )
```

```DAX
Repeat Purchase Rate =
AVERAGE ( mart_executive_kpis[repeat_purchase_rate] )
```

```DAX
Quantity Sold =
SUM ( mart_executive_kpis[total_quantity_sold] )
```

## Customer Measures

```DAX
Customer Lifetime Value =
SUM ( mart_customer_lifetime_value[customer_lifetime_value] )
```

```DAX
Average Customer Lifetime Value =
AVERAGE ( mart_customer_lifetime_value[customer_lifetime_value] )
```

```DAX
Customer Order Count =
SUM ( mart_customer_lifetime_value[order_count] )
```

## Repeat Purchase Measures

```DAX
Repeat Customers =
SUM ( mart_repeat_purchase_metrics[repeat_customers] )
```

```DAX
Repeat Purchase Total Customers =
SUM ( mart_repeat_purchase_metrics[total_customers] )
```

```DAX
Repeat Purchase Rate Summary =
DIVIDE ( [Repeat Customers], [Repeat Purchase Total Customers] )
```

## Monthly Sales Measures

```DAX
Monthly Revenue =
SUM ( mart_sales_monthly[revenue] )
```

```DAX
Monthly Invoice Count =
SUM ( mart_sales_monthly[invoice_count] )
```

```DAX
Monthly Quantity Sold =
SUM ( mart_sales_monthly[quantity_sold] )
```

## Country Measures

```DAX
Revenue by Country =
SUM ( mart_country_revenue[total_revenue] )
```

```DAX
Country Invoice Count =
SUM ( mart_country_revenue[invoice_count] )
```

```DAX
Country Customer Count =
SUM ( mart_country_revenue[customer_count] )
```

```DAX
Country Average Order Value =
DIVIDE ( [Revenue by Country], [Country Invoice Count] )
```

## Formatting Recommendations

- Format revenue and LTV measures as currency.
- Format repeat purchase rate measures as percentage.
- Format invoice/customer/quantity measures as whole numbers.
