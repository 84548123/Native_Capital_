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
        
        # 2. THE BULLETPROOF FETCH: Download independently to avoid all column naming bugs
        print(f"Downloading Nifty 50 data from {start_str}...")
        nifty_data = yf.download("^NSEI", start=start_str, progress=False)
        
        print(f"Downloading Smallcap/Midcap proxy data...")
        smallcap_data = yf.download("^CNXSC", start=start_str, progress=False)
        
        if nifty_data.empty:
            return {"status": "error", "message": "Failed to fetch Nifty 50 data from yfinance."}
            
        if smallcap_data.empty:
            print("Warning: ^CNXSC unavailable today. Falling back to Midcap proxy (^CRSLMD)...")
            smallcap_data = yf.download("^CRSLMD", start=start_str, progress=False)
            if smallcap_data.empty:
                return {"status": "error", "message": "Failed to fetch any Smallcap/Midcap proxies."}

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

        return {
            "status": "success",
            "message": f"Added {len(new_rows)} new trading sessions.",
            "new_rows": len(new_rows)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    result = sync_latest_market_data()
    print(result)