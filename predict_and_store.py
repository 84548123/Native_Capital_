import joblib
import pandas as pd

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
# COLUMN MAPPING
# =====================================

rename_map = {
    "ratio": "Ratio",
    "nifty_return": "Nifty_Return",
    "smallcap_return": "Smallcap_Return",
    "rsi": "Nifty_RSI",
    "momentum20": "Momentum_20D",
    "volatility20": "Volatility_20D",
    "macd": "MACD",
    "macd_signal": "MACD_Signal",
    "trend_strength": "Trend_Strength",
    "regime": "Regime"
}

df.rename(columns=rename_map, inplace=True)

# =====================================
# DERIVED FEATURES
# =====================================

df["EMA_Spread"] = df["ema20"] - df["ema200"]

df["SMA_20_200_Ratio"] = (
    df["sma20"] /
    df["sma200"]
)

# =====================================
# CLEAN
# =====================================

df.replace(
    [float("inf"), -float("inf")],
    pd.NA,
    inplace=True
)

df.dropna(inplace=True)

print("\nRows Available:", len(df))

if len(df) == 0:
    raise Exception(
        "No rows left after cleaning. Check feature columns."
    )

# =====================================
# VERIFY MODEL FEATURES
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
# STORE TO POSTGRESQL
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