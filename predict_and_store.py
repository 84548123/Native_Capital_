
import joblib
import pandas as pd
import numpy as np

from sqlalchemy import text
from datetime import datetime

from database import engine

# =====================================
# LOAD MODEL
# =====================================

payload = joblib.load(
    "outputs/reports/xgb_forecast_model.pkl"
)

model = payload["model"]
features = payload["features"]

print("\n✅ Loaded Model Features Expected:")
print(features)

# =====================================
# LOAD DATA FROM POSTGRESQL
# =====================================

query = """
SELECT *
FROM market_data
ORDER BY date
"""

df = pd.read_sql(query, engine)

print("\n📊 Database Columns Retrieved:")
print(df.columns.tolist())

# =====================================
# COLUMN NORMALIZATION
# =====================================

df.rename(
    columns={
        "nifty50": "Nifty50",
        "smallcap250": "Smallcap250"
    },
    inplace=True
)

# =====================================
# FEATURE ENGINEERING
# =====================================

df["Ratio"] = (
    df["Nifty50"] /
    df["Smallcap250"]
)

df["Nifty_Return"] = (
    df["Nifty50"]
    .pct_change()
)

df["Smallcap_Return"] = (
    df["Smallcap250"]
    .pct_change()
)

# =====================================
# RSI
# =====================================

delta = df["Nifty50"].diff()

gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)

avg_gain = gain.ewm(
    com=13,
    adjust=False
).mean()

avg_loss = loss.ewm(
    com=13,
    adjust=False
).mean()

rs = avg_gain / avg_loss

df["Nifty_RSI"] = (
    100 -
    (100 / (1 + rs))
)

# =====================================
# SMA
# =====================================

df["Nifty_20_SMA"] = (
    df["Nifty50"]
    .rolling(20)
    .mean()
)

df["Nifty_200_SMA"] = (
    df["Nifty50"]
    .rolling(200)
    .mean()
)

df["SMA_20_200_Ratio"] = (
    df["Nifty_20_SMA"] /
    df["Nifty_200_SMA"]
)

# =====================================
# EMA
# =====================================

df["Nifty_20_EMA"] = (
    df["Nifty50"]
    .ewm(
        span=20,
        adjust=False
    )
    .mean()
)

df["Nifty_200_EMA"] = (
    df["Nifty50"]
    .ewm(
        span=200,
        adjust=False
    )
    .mean()
)

df["EMA_Spread"] = (
    df["Nifty_20_EMA"] -
    df["Nifty_200_EMA"]
)

# =====================================
# MOMENTUM
# =====================================

df["Momentum_20D"] = (
    df["Nifty50"] -
    df["Nifty50"].shift(20)
)

# =====================================
# VOLATILITY
# =====================================

df["Volatility_20D"] = (
    df["Nifty_Return"]
    .rolling(20)
    .std()
)

# =====================================
# MACD
# =====================================

ema12 = (
    df["Nifty50"]
    .ewm(
        span=12,
        adjust=False
    )
    .mean()
)

ema26 = (
    df["Nifty50"]
    .ewm(
        span=26,
        adjust=False
    )
    .mean()
)

df["MACD"] = ema12 - ema26

df["MACD_Signal"] = (
    df["MACD"]
    .ewm(
        span=9,
        adjust=False
    )
    .mean()
)

# =====================================
# TREND STRENGTH
# =====================================

df["Trend_Strength"] = (
    abs(df["EMA_Spread"]) /
    df["Nifty50"]
)

# =====================================
# REGIME
# =====================================

df["Regime"] = (
    (
        df["Nifty_20_SMA"] >
        df["Nifty_200_SMA"]
    )
    .astype(int)
)

# =====================================
# CLEAN DATA
# =====================================

df.replace(
    [float("inf"), -float("inf")],
    np.nan,
    inplace=True
)

df.dropna(inplace=True)

print("\nRows Available:", len(df))

if len(df) == 0:
    raise Exception(
        "No rows left after feature engineering."
    )

# =====================================
# VERIFY FEATURES
# =====================================

missing = [
    f for f in features
    if f not in df.columns
]

if missing:
    raise Exception(
        f"Missing Features: {missing}"
    )

# =====================================
# LATEST RECORD
# =====================================

latest = df.iloc[-1]

print("\nLatest Date:")
print(latest["date"])

# =====================================
# BUILD FEATURE VECTOR
# =====================================

X_latest = pd.DataFrame(
    [latest[features]]
)

print("\nFeature Vector:")
print(X_latest)

# =====================================
# PREDICT
# =====================================

prob_up = float(
    model.predict_proba(X_latest)[0][1]
)

prediction = int(prob_up > 0.5)

confidence = float(
    max(prob_up, 1 - prob_up)
)

print("\n======================")
print("IQ200 PREDICTION")
print("======================")

print(
    f"Probability Up: {prob_up:.2%}"
)

print(
    f"Prediction: {'UP' if prediction else 'DOWN'}"
)

print(
    f"Confidence: {confidence:.2%}"
)

# =====================================
# CREATE TABLE IF NEEDED
# =====================================

with engine.begin() as conn:

    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            prediction_date TIMESTAMP,
            model_name VARCHAR(100),
            probability_up DOUBLE PRECISION,
            prediction INTEGER,
            confidence DOUBLE PRECISION
        )
        """)
    )

# =====================================
# STORE PREDICTION
# =====================================

with engine.begin() as conn:

    conn.execute(
        text(
            """
            INSERT INTO predictions
            (
                prediction_date,
                model_name,
                probability_up,
                prediction,
                confidence
            )
            VALUES
            (
                :prediction_date,
                :model_name,
                :probability_up,
                :prediction,
                :confidence
            )
            """
        ),
        {
            "prediction_date": datetime.now(),
            "model_name": "IQ200_XGBOOST",
            "probability_up": prob_up,
            "prediction": prediction,
            "confidence": confidence
        }
    )

print("\n✅ Prediction Stored Successfully")

# =====================================
# VERIFY
# =====================================

verify = pd.read_sql(
    """
    SELECT *
    FROM predictions
    ORDER BY prediction_date DESC
    LIMIT 5
    """,
    engine
)

print("\nLatest Predictions:")
print(verify)

