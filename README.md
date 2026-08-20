<div align=\"center\">

# ⚡ Native Capital
### Institutional Quantitative Intelligence & Adaptive Multi-Asset Allocator

[![Live Demo](https://img.shields.io/badge/Live%20Platform-Google%20Cloud%20Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://native-capital-1035927964593.us-central1.run.app)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**[🌐 Launch Live Web Platform](https://native-capital-1035927964593.us-central1.run.app)** • **[📡 API Swagger Docs](https://native-capital-1035927964593.us-central1.run.app/docs)** • **[📊 Backtesting Engine](https://native-capital-1035927964593.us-central1.run.app)**

---

</div>

## 📌 Executive Overview

**Native Capital** is an institutional quantitative analytics and algorithmic portfolio allocation workstation engineered for Indian equity markets (**Nifty 50 LargeCap** vs. **Nifty SmallCap 250**). 

The platform leverages **Gaussian Hidden Markov Models (HMM)** to detect underlying market volatility regimes, **calibrated XGBoost classifiers** to generate directional conviction signals, **historical crisis stress-testing** to compute crash drawdowns, and an **actionable rebalancing assistant** that translates statistical signals into trade order tickets.

---

## 🏛️ System Architecture

`
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                 NATIVE CAPITAL QUANT ENGINE                                │
│                     FastAPI • SQLAlchemy • SQLite / PostgreSQL • Uvicorn                  │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
┌──────────────────┐                ┌──────────────────┐                 ┌──────────────────┐
│  GAUSSIAN HMM    │                │ QUANT BACKTESTER │                 │ REBALANCE ENGINE │
│  3-State Regime  │                │ Multi-Strategy   │                 │ Real-Time Drift  │
│  Classification  │                │ Scorecards & VaR │                 │ & Trade Tickets  │
└────────┬─────────┘                └────────┬─────────┘                 └────────┬─────────┘
         │                                    │                                    │
         └────────────────────────────────────┼────────────────────────────────────┘
                                              │
                   ┌──────────────────────────▼───────────────────────────┐
                   │          7-TAB REACT QUANTITATIVE DASHBOARD          │
                   │               Vite • Recharts • Lucide               │
                   ├──────────────────────────────────────────────────────┤
                   │ 1. Terminal Overview    • 5. Monte Carlo & VaR       │
                   │ 2. Strategy Backtester  • 6. HMM Regime Matrix       │
                   │ 3. Portfolio Rebalancer • 7. Technical Ledger        │
                   │ 4. Crisis Stress-Tester                              │
                   └──────────────────────────────────────────────────────┘
`

---

## 🌟 Core Quantitative Features

### 1. 🧭 Gaussian Hidden Markov Model (HMM) Regime Detection
Markets exhibit non-stationary behaviors characterized by distinct latent volatility states. Native Capital fits a 3-state continuous Gaussian HMM on historical log-return and volatility series:
* **BULL_TREND**: High positive drift $\mu > 0$, sustained price momentum, low-to-moderate variance.
* **SIDEWAYS_VOLATILE**: Mean-reverting chop, zero drift $\mu \approx 0$, elevated standard deviation.
* **BEAR_MARKET**: Severe negative drift $\mu < 0$, regime volatility spikes, heightened downside tail risk.

P(S_t = j \mid S_{t-1} = i) = A_{ij}

### 2. 💼 Actionable Portfolio Rebalancing Assistant
Translates mathematical regime states and XGBoost conviction into physical buy/sell execution orders:
* **Dynamic Target Weights**:
  * Bull Trend: \%$ SmallCap 250 / \%$ Nifty 50
  * Sideways Volatile: \%$ SmallCap 250 / \%$ Nifty 50 (Risk-Parity)
  * Bear Market: \%$ SmallCap 250 / \%$ Nifty 50 (Defensive Capital Preservation)
* **Execution Ticket Generation**: Calculates exact rupee reallocation amounts, required share unit quantities at live index prices, priority badges (URGENT, RECOMMENDED), and friction estimates (STT + brokerage).
* **1-Click Copy**: Direct export to clipboard for broker order entry.

### 3. 🛡️ Black Swan & Crisis Stress-Testing Engine
Simulates historical and synthetic tail-risk events to quantify portfolio survival:
* **2020 COVID Flash Shock** ($-38\%$ shock, .8\times$ volatility spike)
* **2008 Global Financial Crisis** ($-52\%$ prolonged credit contraction)
* **2022 Inflation & Rate Hike Tightening** ($-18\%$ compression)
* **Custom Sandbox**: Interactive sliders to model custom market drops ($\pm 70\%$) and volatility multipliers.
* **Metrics**: Compares Max Stress Drawdown, Alpha Preserved ($\Delta \text{Drawdown}$ vs Buy-and-Hold), and estimated days to break-even recovery.

### 4. 📈 Multi-Strategy Quantitative Backtester
Simulates and benchmarks 6 portfolio allocation models across 10+ years:
1. **Dynamic Regime Switching Strategy**
2. **Risk Parity (Inverse 60-Day Volatility)**
3. **Trend Following (20/200-Day SMA Golden/Death Cross)**
4. **Static 50:50 Benchmark**
5. **Nifty 50 Buy-and-Hold Index**
6. **Nifty SmallCap 250 Index**

**Institutional Performance Metrics Calculated:**
\text{Sharpe Ratio} = \frac{R_p - R_f}{\sigma_p} \quad (\text{Risk-Free Rate } R_f = 6.5\%)
\text{Sortino Ratio} = \frac{R_p - R_f}{\sigma_d} \quad (\text{Downside Deviation } \sigma_d)
\text{Calmar Ratio} = \frac{\text{CAGR}}{|\text{Max Drawdown}|}

### 5. 🔮 Monte Carlo & Value-at-Risk (VaR) Engine
* **200-Path Stochastic Fan Cone**: Geometric Brownian Motion (GBM) with ML drift calibration.
* **Parametric & Empirical VaR**: Calculates **95% VaR**, **99% VaR**, and **95% Expected Shortfall (CVaR)**.
* **SHAP Feature Importance**: Explains model feature drivers (RSI, 20/200 SMA Ratio, Volatility, Weekly Returns).

---

## 🖥️ Live Dashboard Tour

| Tab | Interface | Key Functions |
|---|---|---|
| 📊 **1. Terminal Overview** | Live Ticker & IQ200 Conviction | Live market ticks, directional ML signal, KPI cards, and ₹13.8L cumulative equity curve. |
| 📈 **2. Strategy Backtester** | Multi-Strategy Comparison | Interactive backtest curves, institutional scorecard table, underwater drawdown area chart. |
| ⚖️ **3. Portfolio Rebalancer** | Trade Execution Tickets | Capital input slider, current vs target weights, drift gauge, and 1-click copy trade tickets. |
| 🛡️ **4. Crisis Stress-Tester** | Black Swan Simulator | Historical shock selector, custom shock sandbox, crash drawdown cards, and recovery days. |
| 🔮 **5. Monte Carlo & VaR** | 200-Path Stochastic Cone | Horizon slider (7-90 days), Vol multiplier (0.5x-3x), 95/99% VaR cards, and SHAP charts. |
| 🧭 **6. HMM Regime Matrix** | Markov Transition Probabilities | Active regime state probabilities, transition probability matrix, 180-day classification history. |
| 🗄️ **7. Technical Ledger** | Searchable Indicator Database | Complete technical matrix (RSI, MACD, Bollinger Bands) with one-click Excel report export. |

---

## 📡 REST API & WebSocket Specifications

### Live API Base URL:
https://native-capital-1035927964593.us-central1.run.app

| Endpoint | Method | Description |
|---|---|---|
| /api/metrics | GET | Cumulative portfolio performance statistics |
| /api/backtest | GET | Multi-strategy comparative equity curves & scorecards |
| /api/rebalance | GET | Computes target weights, allocation drift, and execution tickets |
| /api/stress-test | GET | Simulates crisis drawdown, alpha preserved, and recovery days |
| /api/regime | GET | Active HMM state, posterior probabilities & transition matrix |
| /api/regime-history | GET | Historical regime classification timeline |
| /api/simulate | GET | Monte Carlo risk engine (95%/99% VaR & Expected Shortfall) |
| /api/iq200 | GET | Directional XGBoost machine learning conviction signal |
| /api/raw-data | GET | Technical indicators ledger (RSI, MACD, Bollinger Bands) |
| /api/download-report | GET | Multi-sheet quantitative Excel report export (.xlsx) |
| /api/sync-market | GET | Live data synchronization from NSE via yfinance |
| /api/health | GET | Healthcheck and model diagnostic status |
| /ws/ledger | WS | Real-time WebSocket streaming price and indicator updates |

---

## 🚀 Quick Start & Installation

### Option 1: Local Development (Windows / macOS / Linux)

`ash
# 1. Clone the repository
git clone https://github.com/84548123/Native_Capital_.git
cd Native_Capital_

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start Backend Server (Port 8001)
python server.py

# 4. Start Vite React Frontend (In a new terminal)
cd frontend
npm install
npm run dev
`

Visit the dashboard at [**http://localhost:5173**](http://localhost:5173).

---

### Option 2: Docker Containerization

`ash
# Build production multi-stage image
docker build -t native-capital:latest .

# Run container
docker run -p 8080:8080 -e PORT=8080 native-capital:latest
`

Visit [**http://localhost:8080**](http://localhost:8080).

---

### Option 3: Deploy to Google Cloud Platform (GCP Cloud Run)

`ash
# Deploy with single gcloud command
gcloud run deploy native-capital \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --port 8080
`

---

## 🛠️ Technology Stack

* **Backend Engine**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pandas, NumPy
* **Quantitative & Machine Learning**: hmmlearn (Gaussian HMM), xgboost, scikit-learn, scipy, joblib
* **Frontend Dashboard**: React 18, Vite, Recharts, Lucide React Icons, CSS Modern Dark Theme
* **Cloud & DevOps**: Google Cloud Run, Google Cloud Build, Docker Multi-Stage, GitHub Actions CI/CD

---

## 📄 License & Disclaimer

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

*Disclaimer: Native Capital is an educational and quantitative research software platform. It does not constitute financial, investment, or trading advice. Past performance is not indicative of future market returns.*
