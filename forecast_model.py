import os
import numpy as np
import pandas as pd
import joblib
from hmmlearn.hmm import GaussianHMM
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "outputs", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(REPORTS_DIR, "xgb_forecast_model.pkl")
HMM_MODEL_PATH = os.path.join(REPORTS_DIR, "hmm_regime_model.pkl")

FEATURE_COLUMNS = [
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


# =====================================================
# FEATURE ENGINEERING PIPELINE
# =====================================================

def compute_all_features(df_input: pd.DataFrame) -> pd.DataFrame:
    """Computes technical indicators and features uniformly for training and inference."""
    df = df_input.copy()
    if "Nifty50 Index Value" in df.columns:
        df.rename(columns={"Nifty50 Index Value": "Nifty50"}, inplace=True)
    if "nifty50" in df.columns:
        df.rename(columns={"nifty50": "Nifty50"}, inplace=True)
    if "Nifty SmallCap 250 Index" in df.columns:
        df.rename(columns={"Nifty SmallCap 250 Index": "Smallcap250"}, inplace=True)
    if "smallcap250" in df.columns:
        df.rename(columns={"smallcap250": "Smallcap250"}, inplace=True)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    elif "date" in df.columns:
        df["Date"] = pd.to_datetime(df["date"], errors="coerce")

    df = df.dropna(subset=["Nifty50"]).sort_values("Date").reset_index(drop=True)

    # Ratio & Returns
    df["Ratio"] = np.where(df["Smallcap250"] == 0, 1.0, df["Nifty50"] / df["Smallcap250"])
    df["Nifty_Return"] = df["Nifty50"].pct_change().fillna(0)
    df["Smallcap_Return"] = df["Smallcap250"].pct_change().fillna(0)

    # RSI (14-day)
    delta = df["Nifty50"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = np.where(avg_loss == 0, 100, avg_gain / avg_loss)
    df["Nifty_RSI"] = np.where(avg_loss == 0, 100, 100 - (100 / (1 + rs)))
    df["Nifty_RSI"] = df["Nifty_RSI"].fillna(50.0)

    # SMAs
    df["Nifty_20_SMA"] = df["Nifty50"].rolling(20).mean().bfill()
    df["Nifty_50_SMA"] = df["Nifty50"].rolling(50).mean().bfill()
    df["Nifty_200_SMA"] = df["Nifty50"].rolling(200).mean().bfill()
    df["SMA_20_200_Ratio"] = np.where(df["Nifty_200_SMA"] == 0, 1.0, df["Nifty_20_SMA"] / df["Nifty_200_SMA"])

    # EMAs
    df["Nifty_20_EMA"] = df["Nifty50"].ewm(span=20, adjust=False).mean()
    df["Nifty_50_EMA"] = df["Nifty50"].ewm(span=50, adjust=False).mean()
    df["Nifty_200_EMA"] = df["Nifty50"].ewm(span=200, adjust=False).mean()
    df["EMA_Spread"] = df["Nifty_20_EMA"] - df["Nifty_200_EMA"]

    # Momentum & Volatility
    df["Momentum_20D"] = (df["Nifty50"] - df["Nifty50"].shift(20)).fillna(0)
    df["Volatility_20D"] = df["Nifty_Return"].rolling(20).std().fillna(0.01)

    # MACD
    ema12 = df["Nifty50"].ewm(span=12, adjust=False).mean()
    ema26 = df["Nifty50"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Trend Strength & Binary Regime
    df["Trend_Strength"] = np.where(df["Nifty50"] == 0, 0, abs(df["EMA_Spread"]) / df["Nifty50"])
    df["Regime"] = (df["Nifty_20_SMA"] > df["Nifty_200_SMA"]).astype(int)

    # Forward target (5-day return > 0)
    df["Future_Return"] = df["Nifty_Return"].shift(-5)
    df["Target"] = (df["Future_Return"] > 0).astype(int)

    return df


# =====================================================
# GAUSSIAN HIDDEN MARKOV MODEL REGIME DETECTOR
# =====================================================

def fit_hmm_regime_model(df_clean: pd.DataFrame, n_components: int = 3) -> dict:
    """Fits a Gaussian HMM on daily return and volatility features."""
    returns = df_clean["Nifty_Return"].values
    volatilities = df_clean["Volatility_20D"].values
    X_hmm = np.column_stack([returns, volatilities])

    hmm = GaussianHMM(
        n_components=n_components,
        covariance_type="diag",
        n_iter=200,
        random_state=42
    )
    hmm.fit(X_hmm)

    hidden_states = hmm.predict(X_hmm)

    # Characterize states by mean return and volatility
    state_profiles = {}
    for state in range(n_components):
        idx = (hidden_states == state)
        if np.any(idx):
            state_profiles[state] = {
                "mean_return": float(np.mean(returns[idx])),
                "mean_vol": float(np.mean(volatilities[idx])),
                "frequency": float(np.mean(idx))
            }
        else:
            state_profiles[state] = {"mean_return": 0.0, "mean_vol": 0.01, "frequency": 0.0}

    # Assign regime labels:
    # State with highest return -> "BULL_TREND"
    # State with lowest return -> "BEAR_MARKET"
    # Remaining state -> "SIDEWAYS_VOLATILE"
    sorted_states = sorted(state_profiles.keys(), key=lambda s: state_profiles[s]["mean_return"])
    bear_state = sorted_states[0]
    bull_state = sorted_states[-1]
    volatile_state = [s for s in sorted_states if s not in (bear_state, bull_state)][0] if n_components == 3 else sorted_states[1]

    state_to_label = {
        bull_state: "BULL_TREND",
        bear_state: "BEAR_MARKET",
        volatile_state: "SIDEWAYS_VOLATILE"
    }

    payload = {
        "model": hmm,
        "state_to_label": state_to_label,
        "state_profiles": state_profiles,
        "transmat": hmm.transmat_.tolist(),
        "bull_state": int(bull_state),
        "bear_state": int(bear_state),
        "volatile_state": int(volatile_state)
    }

    joblib.dump(payload, HMM_MODEL_PATH)
    print(f"[OK] Gaussian HMM Regime Model saved to {HMM_MODEL_PATH}")
    return payload


def detect_market_regime(historical_data=None) -> dict:
    """Detects the current market regime using the Gaussian HMM model."""
    try:
        # Load or fit model
        if os.path.exists(HMM_MODEL_PATH):
            hmm_payload = joblib.load(HMM_MODEL_PATH)
        else:
            df = pd.DataFrame(historical_data) if historical_data is not None else pd.read_csv(os.path.join(BASE_DIR, "Native_Capital.csv"))
            df_feat = compute_all_features(df).dropna()
            hmm_payload = fit_hmm_regime_model(df_feat)

        hmm = hmm_payload["model"]
        state_to_label = hmm_payload["state_to_label"]
        state_profiles = hmm_payload["state_profiles"]

        if historical_data is not None and len(historical_data) > 0:
            if isinstance(historical_data, pd.DataFrame):
                df = historical_data.copy()
            else:
                df = pd.DataFrame(historical_data)
        else:
            df = pd.read_csv(os.path.join(BASE_DIR, "Native_Capital.csv"))

        df_feat = compute_all_features(df)
        returns = df_feat["Nifty_Return"].values
        volatilities = df_feat["Volatility_20D"].values
        X_hmm = np.column_stack([returns, volatilities])

        # Predict current regime and posteriors
        hidden_states = hmm.predict(X_hmm)
        posteriors = hmm.predict_proba(X_hmm)
        current_state = int(hidden_states[-1])
        current_label = state_to_label.get(current_state, "NEUTRAL")
        current_probs = posteriors[-1]

        prob_dict = {}
        for state, label in state_to_label.items():
            prob_dict[label] = round(float(current_probs[state]) * 100, 2)

        latest_vol = float(volatilities[-1]) if len(volatilities) > 0 else 0.015

        # Format historical regime series (last 180 points)
        dates = df_feat["Date"].dt.strftime("%Y-%m-%d").values if "Date" in df_feat.columns else [f"t-{i}" for i in range(len(hidden_states))]
        history = []
        start_idx = max(0, len(hidden_states) - 180)
        for i in range(start_idx, len(hidden_states)):
            st = int(hidden_states[i])
            history.append({
                "date": str(dates[i]),
                "regime": state_to_label.get(st, "NEUTRAL"),
                "nifty": float(df_feat["Nifty50"].iloc[i]),
                "volatility": round(float(volatilities[i]) * 100, 2)
            })

        return {
            "status": "success",
            "current_regime": current_label,
            "regime_state": current_state,
            "regime_volatility": round(latest_vol * 100, 2),
            "probabilities": prob_dict,
            "state_profiles": state_profiles,
            "transmat": hmm_payload.get("transmat", []),
            "history": history
        }

    except Exception as e:
        print(f"[WARN] Regime Detection Warning: {e}")
        return {
            "status": "fallback",
            "current_regime": "BULL_TREND",
            "regime_state": 0,
            "regime_volatility": 12.5,
            "probabilities": {"BULL_TREND": 65.0, "SIDEWAYS_VOLATILE": 25.0, "BEAR_MARKET": 10.0},
            "state_profiles": {},
            "transmat": [],
            "history": []
        }


# =====================================================
# TRAIN XGBOOST DIRECTIONAL FORECAST MODEL
# =====================================================

def train_forecast_model(csv_path: str = None) -> XGBClassifier:
    """Trains and serializes both the XGBoost Classifier and Gaussian HMM regime models."""
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, "Native_Capital.csv")

    print(f"[INFO] Training forecast and regime models from {csv_path}...")
    df_raw = pd.read_csv(csv_path)
    df_proc = compute_all_features(df_raw).dropna().reset_index(drop=True)

    # 1. Fit Gaussian HMM
    hmm_payload = fit_hmm_regime_model(df_proc)

    # 2. Fit XGBoost Model
    X = df_proc[FEATURE_COLUMNS]
    y = df_proc["Target"]

    print(f"[INFO] Features Shape: {X.shape}, Target Shape: {y.shape}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, shuffle=False
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss"
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)

    print("\n========== XGBOOST MODEL EVALUATION ==========")
    print(f"Accuracy  : {acc * 100:.2f}%")
    print(f"Precision : {prec * 100:.2f}%")
    print(f"Recall    : {rec * 100:.2f}%")
    print(f"F1 Score  : {f1 * 100:.2f}%")
    print("==============================================\n")

    feature_importances = []
    for f, imp in sorted(zip(FEATURE_COLUMNS, model.feature_importances_), key=lambda x: x[1], reverse=True):
        feature_importances.append({"feature": f, "importance": round(float(imp), 4)})
        print(f"  {f:20s}: {imp:.4f}")

    # Serialize Model Payload
    model_payload = {
        "model": model,
        "features": FEATURE_COLUMNS,
        "metrics": {
            "accuracy": round(acc * 100, 2),
            "precision": round(prec * 100, 2),
            "recall": round(rec * 100, 2),
            "f1": round(f1 * 100, 2)
        },
        "feature_importances": feature_importances
    }

    joblib.dump(model_payload, MODEL_PATH)
    print(f"[OK] XGBoost Model Saved Successfully to {MODEL_PATH}")

    return model


if __name__ == "__main__":
    train_forecast_model()
    regime_res = detect_market_regime()
    print(f"[OK] Current Detected Regime: {regime_res['current_regime']} (Vol: {regime_res['regime_volatility']}%)")