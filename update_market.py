# update_market.py
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# INIT DATABASE CONNECTION
engine = create_engine(
    "postgresql://postgres:15102001@localhost:5432/nativecapital"
)

def sync_live_market():
    try:
        print("📡 Fetching live spot data from NSE...")
        
        # ^NSEI = Nifty 50 | ^CRSM = Nifty Smallcap 250
        tickers = ["^NSEI", "^CRSM"]
        data = yf.download(tickers, period="1d", interval="1m", progress=False)
        
        if data.empty:
            print("⚠️ Market data unavailable. (Are markets open?)")
            return

        closes = data['Close']
        latest = closes.iloc[-1]
        
        nifty_val = float(latest["^NSEI"])
        smallcap_val = float(latest["^CRSM"])
        
        if pd.isna(nifty_val) or pd.isna(smallcap_val):
            print("⚠️ Incomplete data tick received. Retrying later.")
            return

        # NORMALIZE TO TODAY'S DATE
        today_str = datetime.now().strftime("%Y-%m-%d")

        # UPSERT LOGIC (Overwrite today's candle, don't duplicate)
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM market_data WHERE date = :dt"),
                {"dt": today_str}
            )
            
            conn.execute(
                text("""
                INSERT INTO market_data (date, nifty50, smallcap250)
                VALUES (:dt, :nifty, :smallcap)
                """),
                {
                    "dt": today_str,
                    "nifty": nifty_val,
                    "smallcap": smallcap_val
                }
            )
            
        print(f"✅ Live Sync Successful! [{today_str}] Nifty: {nifty_val:.2f} | Smallcap: {smallcap_val:.2f}")

    except Exception as e:
        print(f"❌ Market Sync Error: {e}")

if __name__ == "__main__":
    sync_live_market()