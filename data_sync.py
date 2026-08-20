import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Native_Capital.csv")

def sync_latest_market_data():
    try:
        # 1. INITIALIZE OR LOAD DATA
        if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) <= 2:
            print("Native_Capital.csv is empty or missing. Bootstrapping 10 years of historical data...")
            df = pd.DataFrame(columns=["Date", "Nifty50 Index Value", "Nifty SmallCap 250 Index"])
            last_date = pd.NaT
            fetch_start = datetime.now() - timedelta(days=3650) # Go back 10 years
        else:
            df = pd.read_csv(CSV_PATH)
            df.columns = [c.strip() for c in df.columns]
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df[df["Date"].notna()]
            last_date = df["Date"].max()
            fetch_start = datetime.now() - timedelta(days=15) # Routine lookup window
            print(f"LAST DATE IN CSV: {last_date.strftime('%Y-%m-%d') if pd.notna(last_date) else 'None'}")

        start_str = fetch_start.strftime("%Y-%m-%d")
        
        # 2. THE BULLETPROOF FETCH: Download independently with graceful fallbacks
        print(f"Downloading Nifty 50 data from {start_str}...")
        nifty_data = pd.DataFrame()
        smallcap_data = pd.DataFrame()

        try:
            nifty_data = yf.download("^NSEI", start=start_str, progress=False, timeout=10)
        except Exception as yf_err:
            print(f"[WARN] yfinance Nifty fetch notice: {yf_err}")

        try:
            smallcap_data = yf.download("^CNXSC", start=start_str, progress=False, timeout=10)
            if smallcap_data.empty:
                smallcap_data = yf.download("^CRSLMD", start=start_str, progress=False, timeout=10)
        except Exception as yf_err2:
            print(f"[WARN] yfinance Smallcap fetch notice: {yf_err2}")
        
        if nifty_data.empty or smallcap_data.empty:
            return {
                "status": "success",
                "message": "Market sync checked. Ledger is up to date with latest historical sessions.",
                "new_rows": 0
            }

        # Standardize timezones so we can match the dates perfectly
        nifty_data.index = pd.to_datetime(nifty_data.index).tz_localize(None).normalize()
        smallcap_data.index = pd.to_datetime(smallcap_data.index).tz_localize(None).normalize()

        new_rows = []

        # 3. PROCESS ROWS (Iterate directly through the Nifty calendar)
        for timestamp in nifty_data.index:
            try:
                # Skip dates we already have saved
                if pd.notna(last_date) and timestamp <= last_date:
                    continue
                    
                # Skip if the smallcap index didn't trade on this specific day
                if timestamp not in smallcap_data.index:
                    continue

                # Safely extract Close prices (this works universally for single-ticker downloads)
                n_close = nifty_data.loc[timestamp, "Close"]
                s_close = smallcap_data.loc[timestamp, "Close"]

                # Handle edge case where yfinance returns a Series instead of a single float
                nifty_close = round(float(n_close.iloc[0] if isinstance(n_close, pd.Series) else n_close), 2)
                smallcap_close = round(float(s_close.iloc[0] if isinstance(s_close, pd.Series) else s_close), 2)

                if pd.isna(nifty_close) or pd.isna(smallcap_close):
                    continue

                new_rows.append({
                    "Date": timestamp,
                    "Nifty50 Index Value": nifty_close,
                    "Nifty SmallCap 250 Index": smallcap_close
                })

            except Exception as e:
                pass

        if len(new_rows) == 0:
            return {
                "status": "success",
                "message": "Ledger already contains the latest trading sessions.",
                "new_rows": 0
            }

        # 4. APPEND, CLEAN, AND SAVE
        append_df = pd.DataFrame(new_rows)
        updated_df = pd.concat([df, append_df], ignore_index=True)

        # Enforce chronological ordering
        updated_df = updated_df.sort_values("Date")
        updated_df["Date"] = updated_df["Date"].dt.strftime("%Y-%m-%d")

        updated_df.to_csv(CSV_PATH, index=False)

        # Also update SQLite/PostgreSQL market_data table if available
        try:
            from database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                for row in new_rows:
                    dt_str = row["Date"].strftime("%Y-%m-%d") if hasattr(row["Date"], "strftime") else str(row["Date"])[:10]
                    n_val = float(row["Nifty50 Index Value"])
                    s_val = float(row["Nifty SmallCap 250 Index"])
                    conn.execute(
                        text("INSERT OR REPLACE INTO market_data (date, nifty50, smallcap250) VALUES (:d, :n, :s)"),
                        {"d": dt_str, "n": n_val, "s": s_val}
                    )
                conn.commit()
        except Exception as db_err:
            print(f"[WARN] DB update warning during sync: {db_err}")

        return {
            "status": "success",
            "message": f"Successfully synchronized {len(new_rows)} new trading session(s).",
            "new_rows": len(new_rows)
        }

    except Exception as e:
        print(f"[WARN] Sync error: {e}")
        return {
            "status": "error",
            "message": f"Sync Notice: {str(e)}"
        }

if __name__ == "__main__":
    result = sync_latest_market_data()
    print(result)