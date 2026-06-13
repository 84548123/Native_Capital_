import numpy as np
import pandas as pd
import joblib

from xgboost import XGBClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# =====================================================
# MARKET REGIME DETECTION
# DEPLOYMENT SAFE VERSION
# =====================================================

def detect_market_regime(historical_data):

    return {
        "current_regime": "Neutral",
        "regime_volatility": 0
    }


# =====================================================
# TRAIN FORECAST MODEL
# =====================================================

def train_forecast_model(csv_path):

    df = pd.read_csv(csv_path)

    df.rename(
        columns={
            "Nifty50 Index Value": "Nifty50",
            "Nifty SmallCap 250 Index": "Smallcap250"
        },
        inplace=True
    )

    # =====================================
    # BASIC FEATURES
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
    # TARGET
    # =====================================

    df["Future_Return"] = (
        df["Nifty_Return"]
        .shift(-5)
    )

    df["Target"] = (
        df["Future_Return"] > 0
    ).astype(int)

    # =====================================
    # RSI
    # =====================================

    delta = df["Nifty50"].diff()

    gain = delta.where(
        delta > 0,
        0
    )

    loss = -delta.where(
        delta < 0,
        0
    )

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
    # REGIME FEATURE
    # =====================================

    df["Regime"] = (
        (
            df["Nifty_20_SMA"] >
            df["Nifty_200_SMA"]
        )
        .astype(int)
    )

    # =====================================
    # FEATURES
    # =====================================

    features = [
        "Ratio",
        "Nifty_Return",
        "Smallcap_Return",
        "Nifty_RSI",
        "Momentum_20D",
        "Volatility_20D",
        "EMA_Spread",
        "MACD",
        "MACD_Signal",
        "SMA_20_200_Ratio",
        "Trend_Strength",
        "Regime"
    ]

    # =====================================
    # CLEAN DATA
    # =====================================

    df.dropna(inplace=True)

    X = df[features]

    y = df["Target"]

    print("X Shape:", X.shape)
    print("Y Shape:", y.shape)

    # =====================================
    # SPLIT
    # =====================================

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            shuffle=False
        )
    )

    # =====================================
    # MODEL
    # =====================================

    model = XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    preds = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        preds
    )

    precision = precision_score(
        y_test,
        preds
    )

    recall = recall_score(
        y_test,
        preds
    )

    f1 = f1_score(
        y_test,
        preds
    )

    print("\n========== MODEL RESULTS ==========")

    print(
        "Accuracy:",
        round(
            accuracy * 100,
            2
        ),
        "%"
    )

    print(
        "Precision:",
        round(
            precision * 100,
            2
        ),
        "%"
    )

    print(
        "Recall:",
        round(
            recall * 100,
            2
        ),
        "%"
    )

    print(
        "F1 Score:",
        round(
            f1 * 100,
            2
        ),
        "%"
    )

    print("\nFeature Importance:")

    for f, i in sorted(
        zip(
            features,
            model.feature_importances_
        ),
        key=lambda x: x[1],
        reverse=True
    ):
        print(
            f"{f}: {round(float(i),4)}"
        )

    joblib.dump(
        {
            "model": model,
            "features": features
        },
        "outputs/reports/xgb_forecast_model.pkl"
    )

    print(
        "\nModel Saved Successfully"
    )

    return model


if __name__ == "__main__":

    train_forecast_model(
        "Native_Capital.csv"
    )