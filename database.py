import os
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "native_capital.db")
CSV_PATH = os.path.join(BASE_DIR, "Native_Capital.csv")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.replace(os.sep, '/')}"
    print(f"[INFO] DATABASE_URL not set. Defaulting to local SQLite: {DATABASE_URL}")

# Create engine with proper pooling / connect args
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("[OK] Database Engine Initialized Successfully")


def init_db():
    """Initializes the database tables and seeds them with data from Native_Capital.csv if empty."""
    try:
        with engine.connect() as conn:
            # Create market_data table
            if DATABASE_URL.startswith("sqlite"):
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS market_data (
                    date TEXT PRIMARY KEY,
                    nifty50 REAL NOT NULL,
                    smallcap250 REAL NOT NULL
                );
                """))
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_date TEXT NOT NULL,
                    prediction INTEGER NOT NULL,
                    probability_up REAL NOT NULL,
                    confidence REAL NOT NULL,
                    model_name TEXT NOT NULL
                );
                """))
            else:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS market_data (
                    date DATE PRIMARY KEY,
                    nifty50 DOUBLE PRECISION NOT NULL,
                    smallcap250 DOUBLE PRECISION NOT NULL
                );
                """))
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    prediction_date TIMESTAMP NOT NULL,
                    prediction INT NOT NULL,
                    probability_up FLOAT NOT NULL,
                    confidence FLOAT NOT NULL,
                    model_name VARCHAR(50) NOT NULL
                );
                """))
            conn.commit()

            # Check if market_data has rows; if not, seed from CSV
            result = conn.execute(text("SELECT COUNT(*) FROM market_data")).scalar()
            if result == 0 and os.path.exists(CSV_PATH):
                print("[INFO] Seeding market_data table from Native_Capital.csv...")
                df = pd.read_csv(CSV_PATH)
                df.columns = [c.strip() for c in df.columns]
                df.rename(columns={
                    "Date": "date",
                    "Nifty50 Index Value": "nifty50",
                    "Nifty SmallCap 250 Index": "smallcap250"
                }, inplace=True)
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
                df["date"] = df["date"].dt.strftime("%Y-%m-%d")
                df[["date", "nifty50", "smallcap250"]].to_sql("market_data", engine, if_exists="append", index=False)
                print(f"[OK] Successfully seeded {len(df)} rows into market_data.")

    except Exception as e:
        print(f"[WARN] Database Init Notice: {e}")


# Run table initialization
init_db()

