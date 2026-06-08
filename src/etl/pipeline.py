import os
import yaml
import pandas as pd
from sqlalchemy import create_engine, text

class CustomerIntelligenceETL:
    def __init__(self, config_path="config/config.yaml"):
        """Initializes connection boundaries and extracts path configurations."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        db = self.config["database"]
        self.db_url = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['db_name']}"
        self.engine = create_engine(self.db_url)
        self.raw_path = self.config["paths"]["raw_data_source"]
        self.processed_dir = self.config["paths"]["processed_folder"]

    def extract(self):
        """Extracts text or binary payloads from multi-sheet sources."""
        print(f"🚀 Starting Extraction Phase from: {self.raw_path}")
        
        # Checking for extension type to handle CSV vs multi-sheet Excel files
        if self.raw_path.endswith(('.xlsx', '.xls')):
            xl = pd.ExcelFile(self.raw_path)
            sheets = xl.sheet_names
            print(f"Found {len(sheets)} data partitions: {sheets}")
            
            # Combine both chronological sheets (2009-2010 and 2010-2011)
            df_list = [xl.parse(sheet) for sheet in sheets]
            df_raw = pd.concat(df_list, ignore_index=True)
        else:
            df_raw = pd.read_csv(self.raw_path, encoding="ISO-8859-1")
            
        print(f"📥 Successfully extracted {len(df_raw):,} raw transactional records.")
        return df_raw

    def transform(self, df):
        """Cleans null values, standardizes data types, and structures features."""
        print("🛠️ Starting Transformation & Data Quality Clean Phase...")
        
        # 1. Strip spaces, convert to lowercase, and completely drop spaces/underscores for mapping uniformity
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "").str.replace("_", "")
        
        # 2. Map the compressed raw strings to our unified snake_case schema references
        rename_map = {
            "invoiceno": "invoice_number",
            "invoice": "invoice_number",
            "stockcode": "stock_code",
            "description": "description",
            "quantity": "quantity",
            "invoicedate": "invoice_date",
            "price": "unit_price",
            "unitprice": "unit_price",
            "customerid": "customer_id",
            "country": "country"
        }
        df = df.rename(columns=rename_map)
        
        # 3. Handle Guest Checkouts / Missing ID Column Gracefully
        if "customer_id" not in df.columns:
            print("⚠️ 'customer_id' column missing in raw partition. Initializing empty column for Guest Checkouts.")
            df["customer_id"] = pd.NA

        # Verify mandatory database target keys exist before structural manipulations
        required_keys = ["invoice_number", "stock_code", "description", "invoice_date", "unit_price", "country", "customer_id"]
        for key in required_keys:
            if key not in df.columns:
                raise KeyError(f"❌ Missing critical column link: '{key}'. Processed headers: {list(df.columns)}")

        # 4. Data Cleansing: Remove rows missing key categorical information
        df = df.dropna(subset=["stock_code", "description"])
        
        # 5. Handle Guest Checkouts: Convert identifiers to clean numeric formats safely
        df["customer_id"] = pd.to_numeric(df["customer_id"], errors='coerce')
        df["customer_id"] = df["customer_id"].astype("Int64")
        
        # 6. Type Conversions & Standardizations
        df["quantity"] = df["quantity"].astype(int)
        df["unit_price"] = df["unit_price"].astype(float)
        df["invoice_date"] = pd.to_datetime(df["invoice_date"])
        df["country"] = df["country"].str.strip()
        
        # Strip out pricing test artifacts or anomalies
        df = df[df["unit_price"] >= 0]

        # Flag cancellation invoices (start with 'C')
        df["is_return"] = df["invoice_number"].astype(str).str.startswith("C")
        
        print(f"✅ Data cleaning complete. Outliers filtered. Remaining records: {len(df):,}")
        return df

    def load_warehouse(self, df):
        """Populates Star Schema tables inside PostgreSQL sequentially."""
        print("💾 Initializing Data Warehouse Loading Operations...")

        with self.engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE fact_sales, dim_product, dim_customer, dim_country RESTART IDENTITY CASCADE"))
            conn.commit()

        # --- TABLE 1: dim_country ---
        print("Loading dim_country...")
        countries = pd.DataFrame(df["country"].unique(), columns=["country_name"])
        countries.to_sql("dim_country", self.engine, if_exists="append", index=False, method="multi")

        country_lookup = pd.read_sql("SELECT country_id, country_name FROM dim_country", self.engine)
        df = df.merge(country_lookup, left_on="country", right_on="country_name", how="left")

        # --- TABLE 2: dim_customer ---
        print("Loading dim_customer...")
        valid_customers = df[df["customer_id"].notnull()]["customer_id"].unique()
        customers_df = pd.DataFrame(valid_customers, columns=["customer_id"])
        customers_df.to_sql("dim_customer", self.engine, if_exists="append", index=False, method="multi")

        # --- TABLE 3: dim_product ---
        print("Loading dim_product...")
        products = df.sort_values("invoice_date").groupby("stock_code").agg({
            "description": "last",
            "unit_price": "last"
        }).reset_index().rename(columns={"unit_price": "unit_price_reference"})

        products["description"] = products["description"].str.slice(0, 255)
        products["stock_code"] = products["stock_code"].str.slice(0, 30)
        products = products.dropna(subset=["stock_code"])
        products = products.drop_duplicates(subset=["stock_code"])
        products.to_sql("dim_product", self.engine, if_exists="append", index=False, method="multi")

        # --- TABLE 4: fact_sales ---
        print("Loading fact_sales...")
        valid_stock_codes = set(products["stock_code"].values)
        fact_sales = df[df["stock_code"].isin(valid_stock_codes)]

        fact_sales = fact_sales[[
            "invoice_number", "stock_code", "customer_id",
            "country_id", "quantity", "invoice_date", "unit_price", "is_return"
        ]].copy()
        fact_sales["invoice_number"] = fact_sales["invoice_number"].astype(str).str.slice(0, 20)
        fact_sales["stock_code"] = fact_sales["stock_code"].astype(str).str.slice(0, 30)
        fact_sales.to_sql("fact_sales", self.engine, if_exists="append", index=False, chunksize=10000, method="multi")
        print("🎉 Star Schema ingestion pipeline completed successfully!")

    def run(self):
        """Executes the complete end-to-end data processing workflow."""
        raw_df = self.extract()
        transformed_df = self.transform(raw_df)
        self.load_warehouse(transformed_df)

if __name__ == "__main__":
    etl = CustomerIntelligenceETL()
    etl.run()