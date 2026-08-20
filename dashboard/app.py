# dashboard/app.py
import os
import sys
import pandas as pd
import numpy as np

# Ensure parent directory is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from forecast_model import compute_all_features, detect_market_regime
from quant_engine import run_multi_strategy_backtest, calculate_performance_metrics

try:
    import streamlit as st
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    st = None

def main():
    if st is None:
        print("[WARN] Streamlit or Plotly not installed. Run: pip install streamlit plotly")
        return

    st.set_page_config(
        page_title="Native Capital Quant Terminal",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("⚡ Native Capital — Institutional Quant Terminal")
    st.markdown("Dynamic Multi-Asset Allocation, HMM Market Regime Detection & Monte Carlo Risk Engine")

    csv_path = os.path.join(BASE_DIR, "Native_Capital.csv")
    if not os.path.exists(csv_path):
        st.error(f"Missing {csv_path}")
        return

    df_raw = pd.read_csv(csv_path)
    df_features = compute_all_features(df_raw)
    backtest = run_multi_strategy_backtest(df_features)
    regime = detect_market_regime(df_features)

    # Sidebar
    st.sidebar.header("🕹️ Controls & Parameters")
    horizon = st.sidebar.slider("Forecast Horizon (Days)", 7, 90, 30)
    vol_mult = st.sidebar.slider("Volatility Multiplier", 0.5, 3.0, 1.0, 0.1)

    # Top KPI Metrics
    latest_metrics = backtest.get("latestMetrics", {})
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Return", f"+{latest_metrics.get('totalReturn', 0)}%", f"CAGR: {latest_metrics.get('cagr', 0)}%")
    with col2:
        st.metric("Sharpe Ratio", latest_metrics.get("sharpeRatio", 0), "Rf = 6.5%")
    with col3:
        st.metric("Sortino Ratio", latest_metrics.get("sortinoRatio", 0), "Downside adjusted")
    with col4:
        st.metric("Max Drawdown", f"{latest_metrics.get('maxDrawdown', 0)}%", f"Calmar: {latest_metrics.get('calmarRatio', 0)}")
    with col5:
        st.metric("Market Regime", regime.get("current_regime", "BULL_TREND"), f"Vol: {regime.get('regime_volatility', 0)}%")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Strategy Backtester", "🔮 Monte Carlo VaR", "🗄️ Historical Matrix"])

    with tab1:
        st.subheader("Multi-Strategy Cumulative Growth (₹1,00,000 Base)")
        df_eq = pd.DataFrame(backtest["equityCurves"])
        fig = go.Figure()
        for col in ["Dynamic_Regime", "Risk_Parity", "Static_50_50", "Nifty_50", "Smallcap_250"]:
            if col in df_eq.columns:
                fig.add_trace(go.Scatter(x=df_eq["Date"], y=df_eq[col], mode="lines", name=col.replace("_", " ")))
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Performance Scorecard Matrix")
        scorecard_df = pd.DataFrame(backtest["scorecards"]).T
        st.dataframe(scorecard_df.style.highlight_max(axis=0, color="#00ffcc22"), use_container_width=True)

    with tab2:
        st.subheader(f"Monte Carlo Stochastic Fan ({horizon} Days, {vol_mult}x Volatility)")
        latest = df_features.iloc[-1]
        daily_drift = float(df_features["Daily_Return"].mean())
        daily_vol = float(df_features["Daily_Return"].std()) * vol_mult
        current_val = float(latest.get("Portfolio_Value", 1000000))

        paths = []
        for _ in range(100):
            shocks = np.random.normal(daily_drift, daily_vol, horizon)
            p = [current_val]
            for s in shocks:
                p.append(p[-1] * (1 + s))
            paths.append(p)

        mc_arr = np.array(paths)
        med = np.median(mc_arr, axis=0)
        p5 = np.percentile(mc_arr, 5, axis=0)
        p95 = np.percentile(mc_arr, 95, axis=0)

        fig_mc = go.Figure()
        for p in paths[:20]:
            fig_mc.add_trace(go.Scatter(y=p, mode="lines", line=dict(color="rgba(0,255,204,0.1)"), showlegend=False))
        fig_mc.add_trace(go.Scatter(y=med, mode="lines", name="Median Expected", line=dict(color="#00ffcc", width=3)))
        fig_mc.add_trace(go.Scatter(y=p5, mode="lines", name="5th Percentile (VaR)", line=dict(color="#ef4444", dash="dash")))
        fig_mc.add_trace(go.Scatter(y=p95, mode="lines", name="95th Percentile", line=dict(color="#10b981", dash="dash")))
        fig_mc.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_mc, use_container_width=True)

    with tab3:
        st.subheader("Historical Technical Ledger")
        st.dataframe(df_features.tail(200).iloc[::-1], use_container_width=True)

if __name__ == "__main__":
    main()
