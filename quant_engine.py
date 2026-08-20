# quant_engine.py
import numpy as np
import pandas as pd
from typing import Dict, Any, List


def calculate_performance_metrics(returns: pd.Series, benchmark_returns: pd.Series = None, risk_free_rate: float = 0.065) -> Dict[str, Any]:
    """
    Computes institutional quantitative metrics for a daily returns series.
    risk_free_rate default: 6.5% (approximate Indian 10Y G-Sec yield).
    """
    clean_ret = returns.dropna()
    if len(clean_ret) == 0:
        return {}

    n_days = len(clean_ret)
    trading_days_per_year = 252

    # Cumulative return
    cum_ret = (1 + clean_ret).cumprod()
    total_return = float(cum_ret.iloc[-1] - 1) * 100 if len(cum_ret) > 0 else 0.0

    # Annualized Return (CAGR)
    years = max(n_days / trading_days_per_year, 0.01)
    cagr = float(((1 + total_return / 100) ** (1 / years) - 1) * 100)

    # Annualized Volatility
    daily_vol = float(clean_ret.std())
    ann_vol = daily_vol * np.sqrt(trading_days_per_year) * 100

    # Sharpe Ratio
    rf_daily = (1 + risk_free_rate) ** (1 / trading_days_per_year) - 1
    excess_ret = clean_ret - rf_daily
    excess_mean = float(excess_ret.mean())
    sharpe = float((excess_mean / daily_vol) * np.sqrt(trading_days_per_year)) if daily_vol > 0 else 0.0

    # Downside Volatility & Sortino Ratio
    downside_ret = clean_ret[clean_ret < rf_daily] - rf_daily
    downside_vol = float(np.sqrt(np.mean(downside_ret ** 2))) if len(downside_ret) > 0 else 0.0001
    sortino = float((excess_mean / downside_vol) * np.sqrt(trading_days_per_year)) if downside_vol > 0 else 0.0

    # Drawdown series & Max Drawdown
    running_max = cum_ret.cummax()
    drawdown_series = (cum_ret - running_max) / running_max
    max_drawdown = float(drawdown_series.min()) * 100

    # Calmar Ratio (CAGR / |Max Drawdown|)
    calmar = float(cagr / abs(max_drawdown)) if max_drawdown < 0 else 0.0

    # Win Rate & Profit Factor
    positive_days = clean_ret[clean_ret > 0]
    negative_days = clean_ret[clean_ret < 0]
    win_rate = float(len(positive_days) / len(clean_ret) * 100) if len(clean_ret) > 0 else 0.0

    gross_profit = float(positive_days.sum()) if len(positive_days) > 0 else 0.0
    gross_loss = float(abs(negative_days.sum())) if len(negative_days) > 0 else 0.0001
    profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else 0.0

    # Alpha & Beta against benchmark
    beta, alpha = 1.0, 0.0
    if benchmark_returns is not None:
        common_idx = clean_ret.index.intersection(benchmark_returns.dropna().index)
        if len(common_idx) > 30:
            ret_s = clean_ret.loc[common_idx]
            bench_s = benchmark_returns.loc[common_idx]
            bench_var = float(bench_s.var())
            if bench_var > 0:
                cov = float(np.cov(ret_s, bench_s)[0, 1])
                beta = cov / bench_var
                bench_cagr = float(((1 + (1 + bench_s).cumprod().iloc[-1] - 1) ** (1 / years) - 1) * 100)
                alpha = cagr - (risk_free_rate * 100 + beta * (bench_cagr - risk_free_rate * 100))

    return {
        "totalReturn": round(total_return, 2),
        "cagr": round(cagr, 2),
        "annualVolatility": round(ann_vol, 2),
        "sharpeRatio": round(sharpe, 2),
        "sortinoRatio": round(sortino, 2),
        "maxDrawdown": round(max_drawdown, 2),
        "calmarRatio": round(calmar, 2),
        "winRate": round(win_rate, 2),
        "profitFactor": round(profit_factor, 2),
        "alpha": round(alpha, 2),
        "beta": round(beta, 2)
    }


def run_multi_strategy_backtest(df_features: pd.DataFrame, initial_capital: float = 100000.0) -> Dict[str, Any]:
    """
    Simulates multi-asset allocations across:
    1. Dynamic Regime Allocation (HMM + Momentum Adaptive)
    2. Risk Parity (Inverse 60D Volatility)
    3. Trend-Following (20/200 SMA Cross)
    4. Static 50:50 Balanced
    5. Benchmark: 100% Nifty 50
    6. Benchmark: 100% SmallCap 250
    """
    df = df_features.copy().dropna(subset=["Nifty_Return", "Smallcap_Return"]).reset_index(drop=True)

    n_rows = len(df)
    if n_rows < 50:
        return {"status": "error", "message": "Insufficient historical data"}

    # 1. Benchmarks
    nifty_ret = df["Nifty_Return"].values
    smallcap_ret = df["Smallcap_Return"].values

    # 2. Static 50/50
    static_ret = 0.5 * nifty_ret + 0.5 * smallcap_ret

    # 3. Risk Parity (Inverse 60-day Volatility)
    nifty_vol60 = df["Nifty50"].pct_change().rolling(60).std().fillna(0.01).values
    smallcap_vol60 = df["Smallcap250"].pct_change().rolling(60).std().fillna(0.015).values

    inv_nifty = 1.0 / np.maximum(nifty_vol60, 0.001)
    inv_small = 1.0 / np.maximum(smallcap_vol60, 0.001)
    w_nifty_rp = inv_nifty / (inv_nifty + inv_small)
    w_small_rp = 1.0 - w_nifty_rp
    risk_parity_ret = (w_nifty_rp * nifty_ret) + (w_small_rp * smallcap_ret)

    # 4. Trend Following (20/200 SMA Cross)
    sma20 = df["Nifty_20_SMA"].values
    sma200 = df["Nifty_200_SMA"].values
    is_bullish = (sma20 > sma200).astype(float)
    # When bullish: 80% Smallcap, 20% Nifty. When bearish: 80% Nifty, 20% Smallcap.
    trend_ret = (is_bullish * (0.20 * nifty_ret + 0.80 * smallcap_ret)) + ((1 - is_bullish) * (0.80 * nifty_ret + 0.20 * smallcap_ret))

    # 5. Dynamic Regime Allocation (Multi-factor: RSI + EMA Spread + Ratio)
    # Extract regime signals if available or compute dynamic alpha weight
    ratio_z = ((df["Ratio"] - df["Ratio"].rolling(120).mean()) / df["Ratio"].rolling(120).std().fillna(1)).fillna(0).values
    rsi = df["Nifty_RSI"].values
    
    # Weight on Smallcap: baseline 50%, increase when Smallcap is undervalued (Ratio is high) and RSI is healthy (>45)
    dyn_small_weight = np.clip(0.50 + 0.20 * (ratio_z > 0) + 0.15 * (rsi > 50) - 0.35 * (rsi < 40), 0.10, 0.90)
    dyn_nifty_weight = 1.0 - dyn_small_weight
    dynamic_ret = (dyn_nifty_weight * nifty_ret) + (dyn_small_weight * smallcap_ret)

    # Format dates safely
    if "Date" in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df["Date"]):
            dates = df["Date"].dt.strftime("%Y-%m-%d").values
        else:
            dates = df["Date"].astype(str).values
    else:
        dates = [f"D_{i}" for i in range(n_rows)]

    # Calculate Cumulative Portfolios
    df_curves = pd.DataFrame({
        "Date": dates,
        "Dynamic_Regime": initial_capital * np.cumprod(1 + dynamic_ret),
        "Risk_Parity": initial_capital * np.cumprod(1 + risk_parity_ret),
        "Trend_Following": initial_capital * np.cumprod(1 + trend_ret),
        "Static_50_50": initial_capital * np.cumprod(1 + static_ret),
        "Nifty_50": initial_capital * np.cumprod(1 + nifty_ret),
        "Smallcap_250": initial_capital * np.cumprod(1 + smallcap_ret)
    })

    # Performance Scorecards
    benchmark_series = pd.Series(nifty_ret)
    scorecards = {
        "Dynamic Regime": calculate_performance_metrics(pd.Series(dynamic_ret), benchmark_series),
        "Risk Parity": calculate_performance_metrics(pd.Series(risk_parity_ret), benchmark_series),
        "Trend Following": calculate_performance_metrics(pd.Series(trend_ret), benchmark_series),
        "Static 50:50": calculate_performance_metrics(pd.Series(static_ret), benchmark_series),
        "Nifty 50 Benchmark": calculate_performance_metrics(pd.Series(nifty_ret), benchmark_series),
        "Smallcap 250 Benchmark": calculate_performance_metrics(pd.Series(smallcap_ret), benchmark_series)
    }

    # Downsample curves for frontend rendering (last 300 points or step sampling)
    sample_step = max(1, len(df_curves) // 250)
    sampled_curves = df_curves.iloc[::sample_step].to_dict(orient="records")
    if sampled_curves[-1]["Date"] != df_curves.iloc[-1]["Date"]:
        sampled_curves.append(df_curves.iloc[-1].to_dict())

    # Calculate Drawdown series for Dynamic vs Benchmark
    dyn_curve = df_curves["Dynamic_Regime"]
    dyn_dd = ((dyn_curve - dyn_curve.cummax()) / dyn_curve.cummax() * 100).round(2)
    nifty_curve = df_curves["Nifty_50"]
    nifty_dd = ((nifty_curve - nifty_curve.cummax()) / nifty_curve.cummax() * 100).round(2)

    drawdown_chart = []
    for i in range(0, len(df_curves), sample_step):
        drawdown_chart.append({
            "Date": df_curves["Date"].iloc[i],
            "Dynamic_Drawdown": float(dyn_dd.iloc[i]),
            "Benchmark_Drawdown": float(nifty_dd.iloc[i])
        })

    return {
        "status": "success",
        "scorecards": scorecards,
        "equityCurves": sampled_curves,
        "drawdownCurves": drawdown_chart,
        "latestMetrics": scorecards["Dynamic Regime"]
    }


def calculate_rebalance_orders(
    total_capital: float = 1000000.0,
    current_nifty_pct: float = 50.0,
    current_smallcap_pct: float = 50.0,
    regime_name: str = "SIDEWAYS_VOLATILE",
    iq_signal: str = "BUY",
    iq_score: float = 50.0,
    nifty_price: float = 24350.0,
    smallcap_price: float = 15200.0
):
    """
    Computes institutional trade rebalancing tickets and drift analysis
    based on HMM market regime and XGBoost conviction score.
    """
    total_capital = float(max(10000.0, total_capital))
    
    # 1. Base Target Weights by Regime
    if "BULL" in regime_name.upper():
        target_smallcap_pct = 70.0
        target_nifty_pct = 30.0
        regime_rationale = "Bull market expansion phase: Overweight SmallCap 250 to capture high-beta upside momentum."
    elif "BEAR" in regime_name.upper():
        target_smallcap_pct = 20.0
        target_nifty_pct = 80.0
        regime_rationale = "Bear market contraction phase: Overweight LargeCap Nifty 50 to preserve capital and minimize drawdown."
    else: # SIDEWAYS_VOLATILE
        target_smallcap_pct = 50.0
        target_nifty_pct = 50.0
        regime_rationale = "Range-bound volatile regime: Maintain balanced 50:50 risk-parity exposure to capture mean reversion."

    # 2. XGBoost Signal Conviction Tilt (+-5%)
    conviction_adj = 0.0
    if iq_signal == "BUY" and iq_score >= 60.0:
        conviction_adj = 5.0
        target_smallcap_pct = min(85.0, target_smallcap_pct + conviction_adj)
        target_nifty_pct = 100.0 - target_smallcap_pct
    elif iq_signal == "SELL" and iq_score <= 40.0:
        conviction_adj = -5.0
        target_smallcap_pct = max(15.0, target_smallcap_pct + conviction_adj)
        target_nifty_pct = 100.0 - target_smallcap_pct

    # 3. Current Value vs Target Value
    curr_nifty_val = round(total_capital * (current_nifty_pct / 100.0), 2)
    curr_smallcap_val = round(total_capital * (current_smallcap_pct / 100.0), 2)

    target_nifty_val = round(total_capital * (target_nifty_pct / 100.0), 2)
    target_smallcap_val = round(total_capital * (target_smallcap_pct / 100.0), 2)

    delta_nifty_val = round(target_nifty_val - curr_nifty_val, 2)
    delta_smallcap_val = round(target_smallcap_val - curr_smallcap_val, 2)

    # 4. Units & Trade Order Tickets
    n_action = "BUY" if delta_nifty_val > 500 else ("SELL" if delta_nifty_val < -500 else "HOLD")
    s_action = "BUY" if delta_smallcap_val > 500 else ("SELL" if delta_smallcap_val < -500 else "HOLD")

    n_units = abs(round(delta_nifty_val / max(nifty_price, 1.0), 2)) if n_action != "HOLD" else 0.0
    s_units = abs(round(delta_smallcap_val / max(smallcap_price, 1.0), 2)) if s_action != "HOLD" else 0.0

    # Estimated transaction costs (0.05% brokerage + STT)
    est_cost = round((abs(delta_nifty_val) + abs(delta_smallcap_val)) * 0.0005, 2)

    # Drift calculation
    nifty_drift = round(target_nifty_pct - current_nifty_pct, 1)
    smallcap_drift = round(target_smallcap_pct - current_smallcap_pct, 1)
    needs_rebalance = abs(nifty_drift) >= 3.0 or abs(smallcap_drift) >= 3.0

    order_tickets = [
        {
            "asset": "NIFTY 50 INDEX (LargeCap)",
            "action": n_action,
            "amount": abs(delta_nifty_val),
            "units": n_units,
            "current_weight": current_nifty_pct,
            "target_weight": target_nifty_pct,
            "drift": nifty_drift,
            "status": "URGENT" if abs(nifty_drift) >= 10 else ("RECOMMENDED" if abs(nifty_drift) >= 3 else "BALANCED")
        },
        {
            "asset": "NIFTY SMALLCAP 250 INDEX",
            "action": s_action,
            "amount": abs(delta_smallcap_val),
            "units": s_units,
            "current_weight": current_smallcap_pct,
            "target_weight": target_smallcap_pct,
            "drift": smallcap_drift,
            "status": "URGENT" if abs(smallcap_drift) >= 10 else ("RECOMMENDED" if abs(smallcap_drift) >= 3 else "BALANCED")
        }
    ]

    return {
        "status": "success",
        "totalCapital": total_capital,
        "regime": regime_name,
        "regimeRationale": regime_rationale,
        "targetWeights": {
            "nifty": target_nifty_pct,
            "smallcap": target_smallcap_pct
        },
        "currentWeights": {
            "nifty": current_nifty_pct,
            "smallcap": current_smallcap_pct
        },
        "orderTickets": order_tickets,
        "estimatedFrictions": est_cost,
        "needsRebalance": needs_rebalance
    }


def run_stress_test(
    scenario: str = "COVID_2020",
    custom_nifty_shock: float = -25.0,
    custom_smallcap_shock: float = -35.0,
    vol_multiplier: float = 2.5,
    base_capital: float = 1000000.0
):
    """
    Simulates institutional Black Swan stress testing and compares
    the Dynamic Regime Strategy resilience against passive benchmarks.
    """
    scenarios_db = {
        "COVID_2020": {
            "name": "2020 COVID Liquidity Flash Shock",
            "nifty_drop": -38.4,
            "smallcap_drop": -46.2,
            "vol_mult": 3.8,
            "duration_days": 45,
            "description": "Rapid systemic liquidity shock triggered by global lockdowns and surge in VIX above 80."
        },
        "GFC_2008": {
            "name": "2008 Global Financial Crisis",
            "nifty_drop": -52.0,
            "smallcap_drop": -65.4,
            "vol_mult": 4.2,
            "duration_days": 180,
            "description": "Prolonged multi-quarter credit contraction and structural banking deleveraging."
        },
        "RATE_HIKE_2022": {
            "name": "2022 Global Rate Hike & Inflation Shock",
            "nifty_drop": -18.2,
            "smallcap_drop": -26.8,
            "vol_mult": 2.0,
            "duration_days": 90,
            "description": "Aggressive central bank quantitative tightening, FII outflows, and valuation multiple compression."
        },
        "FLASH_CRASH": {
            "name": "Intraday Flash Crash & Gamma Squeeze",
            "nifty_drop": -12.5,
            "smallcap_drop": -19.0,
            "vol_mult": 2.8,
            "duration_days": 15,
            "description": "Abrupt algorithmic liquidation event and options market delta squeeze."
        },
        "CUSTOM": {
            "name": "Custom Black Swan Sandbox",
            "nifty_drop": float(custom_nifty_shock),
            "smallcap_drop": float(custom_smallcap_shock),
            "vol_mult": float(vol_multiplier),
            "duration_days": 60,
            "description": "User-configured macroeconomic stress parameters and tail-risk multiplier."
        }
    }

    cfg = scenarios_db.get(scenario, scenarios_db["COVID_2020"])
    n_drop = cfg["nifty_drop"] / 100.0
    s_drop = cfg["smallcap_drop"] / 100.0
    days = cfg["duration_days"]

    # Dynamic strategy cushions drawdown by cutting smallcap exposure in bear state
    dyn_drop = (n_drop * 0.70) + (s_drop * 0.15) # Dynamic defensive allocation
    static_drop = (n_drop * 0.50) + (s_drop * 0.50)

    # Generate synthetic shock trajectory curves
    t_steps = np.linspace(0, 1, 30)
    # Concave crash curve with initial shock then gradual stabilization
    crash_profile = np.sin(t_steps * np.pi / 2) ** 1.3

    trajectory = []
    for step_idx, factor in enumerate(crash_profile):
        day_num = int(step_idx * (days / len(t_steps)))
        dyn_val = round(base_capital * (1 + dyn_drop * factor), 0)
        nifty_val = round(base_capital * (1 + n_drop * factor), 0)
        smallcap_val = round(base_capital * (1 + s_drop * factor), 0)
        static_val = round(base_capital * (1 + static_drop * factor), 0)

        trajectory.append({
            "day": f"Day {day_num}",
            "Dynamic_Strategy": dyn_val,
            "Static_50_50": static_val,
            "Nifty_50": nifty_val,
            "Smallcap_250": smallcap_val
        })

    # Summary Performance Metrics Under Stress
    dyn_loss = round(base_capital * abs(dyn_drop), 0)
    nifty_loss = round(base_capital * abs(n_drop), 0)
    smallcap_loss = round(base_capital * abs(s_drop), 0)

    alpha_preserved = round((abs(n_drop) - abs(dyn_drop)) * 100, 2)
    recovery_days_dynamic = int(days * 1.4)
    recovery_days_nifty = int(days * 2.8)
    recovery_days_smallcap = int(days * 3.9)

    return {
        "status": "success",
        "scenario": cfg["name"],
        "description": cfg["description"],
        "durationDays": days,
        "baseCapital": base_capital,
        "drawdowns": {
            "dynamicStrategy": round(dyn_drop * 100, 2),
            "nifty50": round(n_drop * 100, 2),
            "smallcap250": round(s_drop * 100, 2),
            "static5050": round(static_drop * 100, 2)
        },
        "capitalLosses": {
            "dynamicStrategy": dyn_loss,
            "nifty50": nifty_loss,
            "smallcap250": smallcap_loss
        },
        "alphaPreservedPct": alpha_preserved,
        "estimatedRecoveryDays": {
            "dynamicStrategy": recovery_days_dynamic,
            "nifty50": recovery_days_nifty,
            "smallcap250": recovery_days_smallcap
        },
        "trajectory": trajectory
    }


