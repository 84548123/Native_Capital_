# market_features.py

import numpy as np
import pandas as pd


def add_features(df):

    # ==========================================
    # COLUMN NORMALIZATION
    # ==========================================

    rename_map = {
        "nifty50": "Nifty50",
        "smallcap250": "Smallcap250",
        "date": "Date"
    }

    df = df.rename(columns=rename_map)

    # ==========================================
    # BASIC RETURNS
    # ==========================================

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

    # ==========================================
    # RSI (14)
    # ==========================================

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

    # ==========================================
    # SMA
    # ==========================================

    df["Nifty_20_SMA"] = (
        df["Nifty50"]
        .rolling(20)
        .mean()
    )

    df["Nifty_50_SMA"] = (
        df["Nifty50"]
        .rolling(50)
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

    # ==========================================
    # EMA
    # ==========================================

    df["Nifty_20_EMA"] = (
        df["Nifty50"]
        .ewm(span=20, adjust=False)
        .mean()
    )

    df["Nifty_50_EMA"] = (
        df["Nifty50"]
        .ewm(span=50, adjust=False)
        .mean()
    )

    df["Nifty_200_EMA"] = (
        df["Nifty50"]
        .ewm(span=200, adjust=False)
        .mean()
    )

    df["EMA_Spread"] = (
        df["Nifty_20_EMA"] -
        df["Nifty_200_EMA"]
    )

    # ==========================================
    # MOMENTUM
    # ==========================================

    df["Momentum_20D"] = (
        df["Nifty50"] -
        df["Nifty50"].shift(20)
    )

    # ==========================================
    # VOLATILITY
    # ==========================================

    df["Volatility_20D"] = (
        df["Nifty_Return"]
        .rolling(20)
        .std()
    )

    # ==========================================
    # MACD
    # ==========================================

    ema12 = (
        df["Nifty50"]
        .ewm(span=12, adjust=False)
        .mean()
    )

    ema26 = (
        df["Nifty50"]
        .ewm(span=26, adjust=False)
        .mean()
    )

    df["MACD"] = ema12 - ema26

    df["MACD_Signal"] = (
        df["MACD"]
        .ewm(span=9, adjust=False)
        .mean()
    )

    # ==========================================
    # TREND STRENGTH
    # ==========================================

    df["Trend_Strength"] = (
        abs(df["EMA_Spread"]) /
        df["Nifty50"]
    )

    # ==========================================
    # REGIME
    # ==========================================

    df["Regime"] = np.where(
        df["Nifty_20_SMA"] >
        df["Nifty_200_SMA"],
        1,
        0
    )

    return df