"""Streaming ingestion + AI-clean layer for the customer intelligence warehouse.

Live order-event stream -> Redpanda (Kafka API) -> AI-clean gate -> PostgreSQL.
Additive layer: the batch star-schema ETL (src/etl/pipeline.py) is untouched.
"""
