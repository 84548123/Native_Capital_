import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:15102001@localhost:5432/native_capital"

engine = create_engine(DATABASE_URL)

df = pd.read_sql(
    "SELECT * FROM market_data ORDER BY date",
    engine
)

# ==========================
# Returns
# ==========================

df["ratio"] = df["nifty50"] / df["smallcap250"]

df["nifty_return"] = df["nifty50"].pct_change()

df["smallcap_return"] = df["smallcap250"].pct_change()

# ==========================
# RSI
# ==========================

delta = df["nifty50"].diff()

gain = delta.where(delta > 0, 0)

loss = -delta.where(delta < 0, 0)

avg_gain = gain.ewm(com=13, adjust=False).mean()

avg_loss = loss.ewm(com=13, adjust=False).mean()

rs = avg_gain / avg_loss

df["rsi"] = 100 - (100 / (1 + rs))

# ==========================
# SMA
# ==========================

df["sma20"] = df["nifty50"].rolling(20).mean()

df["sma50"] = df["nifty50"].rolling(50).mean()

df["sma200"] = df["nifty50"].rolling(200).mean()

# ==========================
# EMA
# ==========================

df["ema20"] = df["nifty50"].ewm(span=20).mean()

df["ema50"] = df["nifty50"].ewm(span=50).mean()

df["ema200"] = df["nifty50"].ewm(span=200).mean()

# ==========================
# MACD
# ==========================

ema12 = df["nifty50"].ewm(span=12).mean()

ema26 = df["nifty50"].ewm(span=26).mean()

df["macd"] = ema12 - ema26

df["macd_signal"] = (
    df["macd"]
    .ewm(span=9)
    .mean()
)

# ==========================
# Momentum
# ==========================

df["momentum20"] = (
    df["nifty50"]
    - df["nifty50"].shift(20)
)

# ==========================
# Volatility
# ==========================

df["volatility20"] = (
    df["nifty_return"]
    .rolling(20)
    .std()
)

# ==========================
# Trend Strength
# ==========================

df["trend_strength"] = (
    abs(df["ema20"] - df["ema200"])
    / df["nifty50"]
)

# ==========================
# Regime
# ==========================

df["regime"] = (
    (df["sma20"] > df["sma200"])
    .astype(int)
)

df.to_sql(
    "market_data",
    engine,
    if_exists="replace",
    index=False
)

print("Features Updated Successfully")