# seed_market_data.py
import os
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_HjN9nCoaFw7r@ep-patient-mouse-adrleu5e.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL)

CSV_PATH = "Native_Capital.csv"

def seed_database_pipeline():
    try:
        # 1. VERIFY MATERIAL INFRASTRUCTURE
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"Source file '{CSV_PATH}' missing from run directory.")
            
        print("📖 Reading and parsing source CSV data matrix...")
        df = pd.read_csv(CSV_PATH)
        df.columns = [c.strip() for c in df.columns]

        # 2. STANDARDIZE SCHEMAS AND DATATYPES
        df.rename(columns={
            "Date": "date",
            "Nifty50 Index Value": "nifty50",
            "Nifty SmallCap 250 Index": "smallcap250"
        }, inplace=True)

        # Enforce robust pandas datetime parsing
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).copy()
        
        # Sort chronologically to maintain mathematical consistency
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Filter strictly for baseline database injection columns
        df = df[["date", "nifty50", "smallcap250"]]

        # 3. CONSTRUCT ENFORCED DDL SCHEMA (SAFETY NET)
        # This prevents pandas from auto-generating lazy, non-indexed typeless tables
        table_ddl = """
        CREATE TABLE IF NOT EXISTS market_data (
            date DATE PRIMARY KEY,
            nifty50 DOUBLE PRECISION NOT NULL,
            smallcap250 DOUBLE PRECISION NOT NULL
        );
        """

        # 4. EXECUTE ATOMIC TRANSACTION TRANSACTION MATRIX
        print("🏗️  Verifying production table schemas and indexes...")
        with engine.begin() as conn:
            # Enforce the strict schema with explicit data types and index keys
            conn.execute(text(table_ddl))
            
            # Clear historical rows safely without dropping tables, indexes, or constraints
            print("🧹 Truncating stale production rows (preserving schema boundaries)...")
            conn.execute(text("TRUNCATE TABLE market_data;"))

        # 5. EXECUTE BULK DATA INJECTION
        print("🚀 Executing high-speed batched block insertion...")
        df.to_sql(
            "market_data",
            engine,
            if_exists="append", # CRUCIAL: Append preserves constraints and primary key indexes
            index=False,
            method="multi",     # Group insertions into batched blocks to save network roundtrips
            chunksize=1000
        )

        print("\n==========================================")
        print("✅ DATABASE SEEDING COMPLETE")
        print("==========================================")
        print(f"Total Rows Injected: {len(df)}")
        print("\nLatest Matrix Tail View:")
        print(df.tail())

    except Exception as e:
        print(f"\n❌ Seeding Core Terminated Prematurely: {e}")

if __name__ == "__main__":
    seed_database_pipeline()