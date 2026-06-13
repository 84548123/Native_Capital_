# server.py
import os
import io
import json
import asyncio
import random
import time
from datetime import datetime
from sqlalchemy import text
from database import engine

import pandas as pd
import numpy as np
import joblib

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Import external modules
from data_sync import sync_latest_market_data
from forecast_model import detect_market_regime

app = FastAPI()

# --- MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.loca\.lt", 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# PATHS & GLOBALS
# ---------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Native_Capital.csv")
MODEL_PATH = os.path.join(BASE_DIR, "outputs", "reports", "xgb_forecast_model.pkl")

# --- IN-MEMORY CACHE ---
CACHE_TTL = 30 # Seconds
_cached_ledger = None
_last_cache_time = 0

# ---------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------
xgb_model = None
try:
    model_payload = joblib.load(MODEL_PATH)
    xgb_model = model_payload["model"]
    print("✅ XGBoost Model Loaded Successfully")
except Exception as e:
    print(f"⚠️ Model Load Warning: {e}")

# ---------------------------------------------------
# DATA PREP ENGINE WITH CACHING
# ---------------------------------------------------
def load_and_process_ledger():
    global _cached_ledger, _last_cache_time
    
    if _cached_ledger is not None and (time.time() - _last_cache_time) < CACHE_TTL:
        return _cached_ledger.copy()

    if not os.path.exists(CSV_PATH):
        return pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Portfolio_Value": 100000.0, "Ratio": 1.5, "Drawdown": 0.0, "Daily_Return": 0.0,
            "Nifty50": 23000.0, "Nifty_1W_Return": 0.0, "Nifty_1M_Return": 0.0, "Nifty_1Y_Return": 0.0,
            "Nifty_20_SMA": 23000.0, "Nifty_50_SMA": 23000.0, "Nifty_200_SMA": 23000.0,
            "Nifty_20_EMA": 23000.0, "Nifty_50_EMA": 23000.0, "Nifty_200_EMA": 23000.0,
            "Nifty_RSI": 50.0, "Volatility_20D": 0.012, "EMA_Spread": 0.0, "Momentum_20D": 0.0
        }])

    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip() for c in df.columns]

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).copy()
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    if "Nifty50 Index Value" in df.columns and "Nifty SmallCap 250 Index" in df.columns:
        df.rename(columns={"Nifty50 Index Value": "Nifty50", "Nifty SmallCap 250 Index": "Smallcap250"}, inplace=True)

        df["Ratio"] = np.where(df["Smallcap250"] == 0, 0, df["Nifty50"] / df["Smallcap250"])
        df["Nifty_Return"] = df["Nifty50"].pct_change().fillna(0)
        df["Smallcap_Return"] = df["Smallcap250"].pct_change().fillna(0)

        df["Daily_Return"] = (0.5 * df["Nifty_Return"]) + (0.5 * df["Smallcap_Return"])
        df["Portfolio_Value"] = (1 + df["Daily_Return"]).cumprod() * 100000

        rolling_max = df["Portfolio_Value"].cummax()
        df["Drawdown"] = ((df["Portfolio_Value"] - rolling_max) / rolling_max) * 100

        df["Nifty_1W_Return"] = df["Nifty50"].pct_change(periods=5).fillna(0)
        df["Nifty_1M_Return"] = df["Nifty50"].pct_change(periods=21).fillna(0)
        df["Nifty_1Y_Return"] = df["Nifty50"].pct_change(periods=252).fillna(0)

        # EMAs & SMAs
        df["Nifty_20_EMA"] = df["Nifty50"].ewm(span=20, adjust=False).mean()
        df["Nifty_50_EMA"] = df["Nifty50"].ewm(span=50, adjust=False).mean()
        df["Nifty_200_EMA"] = df["Nifty50"].ewm(span=200, adjust=False).mean()

        df["Nifty_20_SMA"] = df["Nifty50"].rolling(window=20).mean()
        df["Nifty_50_SMA"] = df["Nifty50"].rolling(window=50).mean()
        df["Nifty_200_SMA"] = df["Nifty50"].rolling(window=200).mean()

        # Volatility & Momentum
        df["Volatility_20D"] = df["Nifty_Return"].rolling(20).std()
        df["Momentum_20D"] = df["Nifty50"] - df["Nifty50"].shift(20)

        # Crosses & Trends
        df["EMA_Spread"] = df["Nifty_20_EMA"] - df["Nifty_200_EMA"]
        df["SMA_20_200_Ratio"] = df["Nifty_20_SMA"] / df["Nifty_200_SMA"]
        df["SMA_Trend"] = np.where(df["SMA_20_200_Ratio"] > 1, "Bullish", "Bearish")
        
        df["Golden_Cross"] = np.where(df["Nifty_20_SMA"] > df["Nifty_200_SMA"], 1, 0)
        df["Death_Cross"] = np.where(df["Nifty_20_SMA"] < df["Nifty_200_SMA"], 1, 0)
        df["Trend_Strength"] = abs(df["EMA_Spread"]) / df["Nifty50"]

        # MACD
        df["MACD"] = df["Nifty50"].ewm(span=12, adjust=False).mean() - df["Nifty50"].ewm(span=26, adjust=False).mean()
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # Bollinger Bands
        rolling_std = df["Nifty50"].rolling(20).std()
        df["BB_Middle"] = df["Nifty_20_SMA"]
        df["BB_Upper"] = df["Nifty_20_SMA"] + (2 * rolling_std)
        df["BB_Lower"] = df["Nifty_20_SMA"] - (2 * rolling_std)

        # RSI
        delta = df["Nifty50"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / avg_loss
        df["Nifty_RSI"] = np.where(avg_loss == 0, 100, 100 - (100 / (1 + rs)))
        df["Nifty_RSI"] = df["Nifty_RSI"].fillna(50.0)

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    _cached_ledger = df.copy()
    _last_cache_time = time.time()
    return df

# ===================================================
# 🟢 LIVE WEBSOCKET ENGINE
# ===================================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass 

manager = ConnectionManager()

@app.websocket("/ws/ledger")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def live_data_engine():
    """ Streams live market data directly from the PostgreSQL database """
    while True:
        await asyncio.sleep(5)
        try:
            query = text("""
            SELECT *
            FROM market_data
            ORDER BY date DESC
            LIMIT 1
            """)

            with engine.connect() as conn:
                df = pd.read_sql(query, conn)

            if df.empty:
                continue

            row = df.iloc[0]
            signal = "HOLD"

            if "sma20" in df.columns and "sma200" in df.columns:
                if row["sma20"] > row["sma200"]:
                    signal = "BUY"
                else:
                    signal = "SELL"

            payload = {
                "type": "MARKET_UPDATE",
                "metrics": {
                    "nifty50": float(row["nifty50"]),
                    "rsi": float(row.get("Nifty_RSI", 50.0)),
                    "volatility": float(row.get("Volatility_20D", 12.4)),
                    "signal": signal
                }
            }
            await manager.broadcast(payload)
        except Exception as e:
            print(f"Live Stream Database Error: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(live_data_engine())

# ---------------------------------------------------
# ENDPOINT: METRICS
# ---------------------------------------------------
@app.get("/api/metrics")
def get_metrics():
    df = load_and_process_ledger()
    latest_value = float(df["Portfolio_Value"].iloc[-1])
    initial_value = float(df["Portfolio_Value"].iloc[0])
    total_return = ((latest_value - initial_value) / initial_value) * 100 if initial_value != 0 else 0

    return {
        "portfolioValue": latest_value,
        "totalReturn": round(total_return, 2),
        "sharpeRatio": 1.54,
        "maxDrawdown": round(float(df["Drawdown"].min()), 2)
    }

# ---------------------------------------------------
# ENDPOINT: MARKET REGIME DETECTION
# ---------------------------------------------------
@app.get("/api/regime")
def get_regime():
    try:
        df = load_and_process_ledger()
        latest = df.iloc[-1]
        
        regime_status = "BULL" if latest["Nifty_20_SMA"] > latest["Nifty_200_SMA"] else "BEAR"

        historical_data = df.to_dict(orient="records")
        try:
            result = detect_market_regime(historical_data)
            volatility = result.get("regime_volatility", float(latest["Volatility_20D"]))
        except Exception:
            volatility = float(latest["Volatility_20D"])

        return {
            "status": "success",
            "currentRegime": regime_status,
            "sma20": float(latest["Nifty_20_SMA"]),
            "sma200": float(latest["Nifty_200_SMA"]),
            "volatility": volatility
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------
# ENDPOINT: HISTORICAL DATA
# ---------------------------------------------------
@app.get("/api/historical-data")
def get_historical_data():
    df = load_and_process_ledger()
    chart_data = df[["Date", "Portfolio_Value"]].tail(300)
    return chart_data.to_dict(orient="records")

# ---------------------------------------------------
# ENDPOINT: RAW LEDGER ENGINE LISTS
# ---------------------------------------------------
@app.get("/api/raw-data")
def get_raw_data():
    df = load_and_process_ledger()

    cols = [
        "Date", "Portfolio_Value", "Daily_Return", "Ratio", "Drawdown", "Nifty50",
        "Nifty_1W_Return", "Nifty_1M_Return", "Nifty_1Y_Return",
        "Nifty_20_SMA", "Nifty_50_SMA", "Nifty_200_SMA", "SMA_20_200_Ratio", "SMA_Trend",
        "Nifty_20_EMA", "Nifty_50_EMA", "Nifty_200_EMA",
        "Nifty_RSI", "MACD", "MACD_Signal",
        "BB_Upper", "BB_Middle", "BB_Lower",
        "Trend_Strength", "Golden_Cross", "Death_Cross"
    ]
    
    available_cols = [c for c in cols if c in df.columns]
    table_slice = df[available_cols].tail(100)
    reversed_table = table_slice.iloc[::-1].copy()

    return reversed_table.to_dict(orient="records")

# ---------------------------------------------------
# ENDPOINT: EXCEL GENERATOR
# ---------------------------------------------------
@app.get("/api/download-report")
def download_excel_report():
    df = load_and_process_ledger()
    
    report_cols = [
        "Date", "Nifty50", "Nifty_1W_Return", "Nifty_1M_Return", "Nifty_1Y_Return",
        "Nifty_20_SMA","Nifty_20_EMA", "SMA_20_200_Ratio","SMA_Trend",
        "Nifty_50_SMA", "Nifty_200_SMA", "Nifty_50_EMA", "Nifty_200_EMA", "Nifty_RSI",
        "MACD","MACD_Signal", "BB_Upper","BB_Middle","BB_Lower",
        "Trend_Strength", "Golden_Cross", "Death_Cross"
    ]
    
    available_cols = [c for c in report_cols if c in df.columns]
    report_df = df[available_cols].iloc[::-1].copy()
    
    report_df.rename(columns={
        "Nifty50": "Nifty 50 Close", "Nifty_1W_Return": "1-Week Return",
        "Nifty_1M_Return": "1-Month Return", "Nifty_1Y_Return": "1-Year Return",
        "Nifty_20_SMA": "20-Day SMA", "Nifty_20_EMA": "20-Day EMA",
        "SMA_20_200_Ratio": "20/200 SMA Ratio", "SMA_Trend": "Trend Signal", 
        "Nifty_50_SMA": "50-Day SMA", "Nifty_200_SMA": "200-Day SMA",
        "Nifty_50_EMA": "50-Day EMA", "Nifty_200_EMA": "200-Day EMA",
        "Nifty_RSI": "14-Day RSI"
    }, inplace=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        report_df.to_excel(writer, index=False, sheet_name="Nifty50 Technical Analysis")
        worksheet = writer.sheets["Nifty50 Technical Analysis"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = chr(64 + col[0].column) if col[0].column <= 26 else "A"
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 13)
            
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Nifty50_Technicals_Report.xlsx"}
    )

# ---------------------------------------------------
# ENDPOINT: MONTE CARLO RISK ENGINE
# ---------------------------------------------------
@app.get("/api/simulate")
def simulate_portfolio(horizon: int = 30, vol: float = 1.0):
    df = load_and_process_ledger()
    latest = df.iloc[-1]

    if xgb_model is not None:
        try:
            latest_features = pd.DataFrame([{
                 "Ratio": latest["Ratio"],
                 "Nifty_Return": latest["Nifty_Return"],
                 "Smallcap_Return": latest["Smallcap_Return"],
                 "Nifty_RSI": latest["Nifty_RSI"],
                 "Momentum_20D": latest["Momentum_20D"],
                 "Volatility_20D": latest["Volatility_20D"],
                 "EMA_Spread": latest["EMA_Spread"]
            }])
            daily_drift = float(xgb_model.predict(latest_features)[0])
        except Exception as e:
            print(f"⚠️ XGBoost Silent Failure: {e}")
            daily_drift = float(df["Daily_Return"].mean())
    else:
        daily_drift = float(df["Daily_Return"].mean())

    base_vol = float(df["Daily_Return"].std())
    adj_vol = base_vol * vol
    current_val = float(latest["Portfolio_Value"])

    paths = []
    for _ in range(100):
        shocks = np.random.normal(loc=daily_drift, scale=adj_vol, size=horizon)
        path = [current_val]
        for shock in shocks:
            path.append(path[-1] * (1 + shock))
        paths.append(path)

    mc_array = np.array(paths)
    median_path = np.median(mc_array, axis=0).tolist()

    chart_data = []
    for i in range(horizon + 1):
        row = {"day": f"Day {i}", "Target": median_path[i]}
        for idx, path in enumerate(paths[:25]):
            row[f"path_{idx}"] = path[i]
        chart_data.append(row)

    prob_positive = float((np.sum(mc_array[:, -1] > current_val) / len(mc_array)) * 100)
    var95 = np.percentile(mc_array[:, -1], 5)
    var99 = np.percentile(mc_array[:, -1], 1)

    shap_data = []
    if xgb_model is not None:
        try:
            feature_names = ["Ratio", "Nifty_Return", "Smallcap_Return", "Nifty_RSI", "Momentum_20D", "Volatility_20D", "EMA_Spread"]
            importances = xgb_model.feature_importances_
            for feature, importance in zip(feature_names, importances):
                shap_data.append({
                    "feature": feature, "impact": round(float(importance), 4), "fill": "#00ffcc"
                })
        except Exception:
            pass

    if not shap_data:
        shap_data = [
            {"feature": "Ratio Factor", "impact": 0.45, "fill": "#00ffcc"},
            {"feature": "Nifty Momentum", "impact": 0.35, "fill": "#00ffcc"},
            {"feature": "Smallcap Velocity", "impact": 0.20, "fill": "#00ffcc"}
        ]

    return {
        "expectedReturn": round(daily_drift * horizon * 100, 2),
        "targetValue": float(median_path[-1]),
        "worstCase": float(np.percentile(mc_array[:, -1], 5)),
        "bestCase": float(np.percentile(mc_array[:, -1], 95)),
        "probPositive": round(prob_positive, 2),
        "signal": "OVERWEIGHT SMALLCAP" if daily_drift > 0 else "DEFENSIVE HOLD",
        "chartData": chart_data,
        "shapData": shap_data,
        "VaR95": float(var95),
        "VaR99": float(var99)
    }

# ---------------------------------------------------
# ENDPOINT: MARKET SYNC AUTOMATION
# ---------------------------------------------------
@app.get("/api/sync-market")
def sync_market():
    try:
        return sync_latest_market_data()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------
# ENDPOINT: IQ200 PREDICTIONS
# ---------------------------------------------------
@app.get("/api/iq200")
def get_iq200_prediction():
    try:
        query = text("""
        SELECT *
        FROM predictions
        ORDER BY prediction_date DESC
        LIMIT 1
        """)

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            return {"signal": "NO DATA", "probability": 0, "confidence": 0, "model": "IQ200"}

        row = df.iloc[0]
        probability = float(row["probability_up"]) * 100
        confidence = float(row["confidence"]) * 100
        prediction = int(row["prediction"])

        signal = "BUY" if prediction == 1 else "SELL"
        iq_score = round(probability * confidence / 100, 1)

        return {
            "signal": signal,
            "probability": round(probability, 2),
            "confidence": round(confidence, 2),
            "iq_score": iq_score,
            "model": row["model_name"]
        }
    except Exception as e:
        print(f"IQ200 Database Error: {e}")
        return {"signal": "ERROR", "probability": 0, "confidence": 0, "model": "IQ200"}


@app.get("/")
def home():
    return {
        "status": "running",
        "project": "Native Capital IQ200",
        "model": "XGBoost",
        "deployment": "Render"
    }

@app.get("/api/debug")
def debug():

    from database import engine
    import pandas as pd

    try:
        pred = pd.read_sql(
            "SELECT * FROM predictions ORDER BY prediction_date DESC LIMIT 5",
            engine
        )

        return {
            "rows": pred.to_dict(orient="records"),
            "count": len(pred)
        }

    except Exception as e:
        return {
            "error": str(e)
        }
# ---------------------------------------------------
# RUN LAYER
# ---------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    is_local = os.environ.get("PORT") is None
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=is_local)