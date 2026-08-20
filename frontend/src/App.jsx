// src/App.jsx
import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, Legend
} from 'recharts';
import {
  LayoutDashboard, TrendingUp, Database, Activity, RefreshCw,
  FileSpreadsheet, Radio, GitCompare, Compass, ShieldAlert,
  ArrowUpRight, ArrowDownRight, Layers, Sliders, CheckCircle2,
  Scale, Flame, Copy, Check, ShieldCheck, AlertTriangle
} from 'lucide-react';
import initialData from './initialData.json';
import './App.css';

// Dynamic API and WebSocket Base URLs (auto-detect local proxy vs direct vs production)
const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE_URL = import.meta.env.VITE_API_URL || (isLocal ? "" : "https://native-capital.onrender.com");
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const WS_BASE_URL = import.meta.env.VITE_WS_URL || (isLocal ? `${wsProtocol}//${window.location.host}/ws/ledger` : "wss://native-capital.onrender.com/ws/ledger");

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [metrics, setMetrics] = useState({
    portfolioValue: 1380952,
    totalReturn: 1280.95,
    cagr: 13.44,
    sharpeRatio: 0.42,
    sortinoRatio: 0.37,
    maxDrawdown: -68.36,
    calmarRatio: 0.2,
    winRate: 57.56,
    profitFactor: 1.14,
    alpha: 1.66,
    beta: 0.9,
    annualVolatility: 19.93
  });
  const [chartData, setChartData] = useState(initialData.chartData || []);
  const [tableData, setTableData] = useState(initialData.tableData || []);
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');

  // Backtester State
  const [backtestData, setBacktestData] = useState(initialData.backtestData || null);
  const [selectedStrategies, setSelectedStrategies] = useState({
    "Dynamic Regime": true,
    "Risk Parity": true,
    "Trend Following": false,
    "Static 50:50": true,
    "Nifty 50 Benchmark": true,
    "Smallcap 250 Benchmark": false
  });

  // Rebalancer State (NEW)
  const [rebCapital, setRebCapital] = useState(1000000);
  const [currentNiftySplit, setCurrentNiftySplit] = useState(50);
  const [rebalanceData, setRebalanceData] = useState(initialData.rebalanceData || null);
  const [copiedTickets, setCopiedTickets] = useState(false);

  // Stress-Tester State (NEW)
  const [activeScenario, setActiveScenario] = useState('COVID_2020');
  const [customNiftyShock, setCustomNiftyShock] = useState(-25);
  const [customSmallcapShock, setCustomSmallcapShock] = useState(-35);
  const [volMultiplier, setVolMultiplier] = useState(2.5);
  const [stressData, setStressData] = useState(initialData.stressTestData || null);

  // Forecast & Monte Carlo State
  const [simData, setSimData] = useState(initialData.simData || {
    expectedReturn: 3.5,
    targetValue: 1420000,
    worstCase: 1250000,
    bestCase: 1600000,
    probPositive: 64.5,
    signal: "OVERWEIGHT SMALLCAP",
    chartData: [],
    shapData: [],
    VaR95: 1255161,
    VaR99: 1180000,
    CVaR95: 1220000
  });
  const [horizon, setHorizon] = useState(30);
  const [volatility, setVolatility] = useState(1.0);
  const [activeModel, setActiveModel] = useState('Ensemble');

  // Live WebSocket & Regime States
  const [liveData, setLiveData] = useState({
    nifty50: 24350.0,
    rsi: "52.4",
    volatility: "12.50",
    signal: "BUY",
    smaTrend: "Bullish",
    timestamp: "Live"
  });
  const [streamConnected, setStreamConnected] = useState(false);
  const [iq200, setIq200] = useState({
    signal: "BUY",
    probability: 69.2,
    confidence: 78.4,
    iq_score: 54.25,
    model: "XGBoost Directional IQ200"
  });
  const [regime, setRegime] = useState({
    currentRegime: "SIDEWAYS_VOLATILE",
    probabilities: { "BULL_TREND": 0.01, "SIDEWAYS_VOLATILE": 99.88, "BEAR_MARKET": 0.11 },
    volatility: 0.85,
    sma20: 23800,
    sma200: 24977,
    smaRatio: 0.9529
  });
  const [regimeHistory, setRegimeHistory] = useState(initialData.regimeHistory || []);

  // 1. Initial HTTP Data Load
  useEffect(() => {
    const fetchData = async () => {
      try {
        const fetchSafe = (url) => fetch(url).then(r => r.ok ? r.json() : null).catch(() => null);

        const [mRes, cRes, tRes, iqRes, regRes, btRes, regHistRes] = await Promise.all([
          fetchSafe(`${API_BASE_URL}/api/metrics`),
          fetchSafe(`${API_BASE_URL}/api/historical-data?points=350`),
          fetchSafe(`${API_BASE_URL}/api/raw-data?limit=150`),
          fetchSafe(`${API_BASE_URL}/api/iq200`),
          fetchSafe(`${API_BASE_URL}/api/regime`),
          fetchSafe(`${API_BASE_URL}/api/backtest`),
          fetchSafe(`${API_BASE_URL}/api/regime-history`)
        ]);

        if (mRes) setMetrics(mRes);
        if (cRes) setChartData(cRes);
        if (tRes) setTableData(tRes);
        if (iqRes) setIq200(iqRes);
        if (regRes) setRegime(regRes);
        if (btRes) setBacktestData(btRes);
        if (regHistRes?.history) setRegimeHistory(regHistRes.history);

        if (tRes && tRes.length > 0) {
          const latest = tRes[0];
          setLiveData({
            nifty50: Number(latest.Nifty50 || 24000),
            rsi: Number(latest.Nifty_RSI || 50).toFixed(1),
            volatility: Number(regRes?.volatility || 12.5).toFixed(2),
            signal: latest.SMA_Trend === "Bullish" ? "BUY" : "SELL",
            smaTrend: latest.SMA_Trend || "Bullish",
            timestamp: "Live"
          });
        }
      } catch (err) {
        console.error("[API Load Warning]", err);
      }
    };

    fetchData();
  }, []);

  // 2. Dynamic Rebalance Query
  useEffect(() => {
    const currentSmallcapSplit = 100 - currentNiftySplit;
    fetch(`${API_BASE_URL}/api/rebalance?capital=${rebCapital}&current_nifty=${currentNiftySplit}&current_smallcap=${currentSmallcapSplit}`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data && data.status === "success") setRebalanceData(data); })
      .catch(() => {});
  }, [rebCapital, currentNiftySplit]);

  // 3. Dynamic Stress Test Query
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/stress-test?scenario=${activeScenario}&nifty_shock=${customNiftyShock}&smallcap_shock=${customSmallcapShock}&vol_mult=${volMultiplier}&capital=${rebCapital}`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data && data.status === "success") setStressData(data); })
      .catch(() => {});
  }, [activeScenario, customNiftyShock, customSmallcapShock, volMultiplier, rebCapital]);

  // 4. Monte Carlo Simulation Query
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/simulate?horizon=${horizon}&vol=${volatility}&model=${activeModel}`)
      .then(res => res.json())
      .then(data => setSimData(data))
      .catch(err => console.error("[Sim Error]", err));
  }, [horizon, volatility, activeModel]);

  // 3. WebSocket Live Feed
  useEffect(() => {
    let socket = null;
    let reconnectTimeout = null;

    const connect = () => {
      try {
        socket = new WebSocket(WS_BASE_URL);
        socket.onopen = () => setStreamConnected(true);
        socket.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);
            if (payload.type === "MARKET_UPDATE") {
              setLiveData(payload.metrics);
            }
          } catch (e) {
            console.error("WS Parse Error", e);
          }
        };
        socket.onclose = () => {
          setStreamConnected(false);
          reconnectTimeout = setTimeout(connect, 3500);
        };
        socket.onerror = () => socket.close();
      } catch (e) {
        reconnectTimeout = setTimeout(connect, 3500);
      }
    };

    connect();
    return () => {
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  const handleLiveSync = () => {
    setIsSyncing(true);
    fetch(`${API_BASE_URL}/api/sync-market`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        alert(data.message || "Market data sync complete.");
        if (data.status === "success" && data.new_rows > 0) window.location.reload();
      })
      .catch((err) => alert(err.message || "Market sync complete."))
      .finally(() => setIsSyncing(false));
  };

  const copyOrderTickets = () => {
    if (!rebalanceData?.orderTickets) return;
    const text = rebalanceData.orderTickets.map(t => 
      `[${t.action}] ${t.asset} | Amount: ₹${t.amount.toLocaleString('en-IN')} | Units: ${t.units} | Target Weight: ${t.target_weight}%`
    ).join('\n');
    navigator.clipboard.writeText(text);
    setCopiedTickets(true);
    setTimeout(() => setCopiedTickets(false), 2500);
  };

  const filteredTableData = useMemo(() => {
    if (!searchFilter.trim()) return tableData;
    const query = searchFilter.toLowerCase();
    return tableData.filter(row =>
      (row.Date && row.Date.toLowerCase().includes(query)) ||
      (row.SMA_Trend && row.SMA_Trend.toLowerCase().includes(query))
    );
  }, [tableData, searchFilter]);

  const strategyColors = {
    "Dynamic Regime": "#00ffcc",
    "Risk Parity": "#38bdf8",
    "Trend Following": "#eab308",
    "Static 50:50": "#a855f7",
    "Nifty 50 Benchmark": "#ef4444",
    "Smallcap 250 Benchmark": "#f97316"
  };

  if (!metrics || !simData) {
    return (
      <div className="loading-screen">
        <Activity size={40} className="animate-spin text-cyan-400" />
        <h2>Initializing Native Capital Quant Engine...</h2>
        <p>Calibrating HMM regimes, neural indicators, and live market feed</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* SIDEBAR NAVIGATION */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-logo">
            <Activity color="#00ffcc" size={26} />
          </div>
          <div>
            <h2>Native Capital</h2>
            <span className="brand-sub">QUANTITATIVE INTELLIGENCE</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <LayoutDashboard size={19} />
            <span>Terminal Overview</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'backtest' ? 'active' : ''}`}
            onClick={() => setActiveTab('backtest')}
          >
            <GitCompare size={19} />
            <span>Strategy Backtester</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'rebalance' ? 'active' : ''}`}
            onClick={() => setActiveTab('rebalance')}
          >
            <Scale size={19} />
            <span>Portfolio Rebalancer</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'stress' ? 'active' : ''}`}
            onClick={() => setActiveTab('stress')}
          >
            <Flame size={19} />
            <span>Crisis Stress-Tester</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'forecast' ? 'active' : ''}`}
            onClick={() => setActiveTab('forecast')}
          >
            <TrendingUp size={19} />
            <span>Monte Carlo & VaR</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'regime' ? 'active' : ''}`}
            onClick={() => setActiveTab('regime')}
          >
            <Compass size={19} />
            <span>HMM Regime Matrix</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'data' ? 'active' : ''}`}
            onClick={() => setActiveTab('data')}
          >
            <Database size={19} />
            <span>Technical Ledger</span>
          </button>
        </nav>

        {/* FEED STATUS */}
        <div className="sidebar-footer">
          <div className="status-badge-container">
            <Radio size={14} className={streamConnected ? 'pulse-live' : 'pulse-off'} />
            <span>{streamConnected ? 'LIVE FEED ACTIVE' : 'LOCAL SIMULATOR'}</span>
          </div>
          <p className="system-version">v2.0 • HMM + XGBoost</p>
        </div>
      </aside>

      {/* MAIN VIEWPORT */}
      <main className="main-content">
        {/* GLOBAL REAL-TIME TICKER TAPE */}
        <header className="global-ticker-tape">
          <div className="ticker-item">
            <span className="ticker-label">NIFTY 50</span>
            <span className="ticker-val text-white">
              ₹{liveData ? Number(liveData.nifty50).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '24,350.00'}
            </span>
          </div>

          <div className="ticker-item">
            <span className="ticker-label">14D RSI</span>
            <span className="ticker-val text-cyan">
              {liveData ? liveData.rsi : '52.4'}
            </span>
          </div>

          <div className="ticker-item">
            <span className="ticker-label">MARKET VOL</span>
            <span className="ticker-val text-purple">
              {liveData ? `${liveData.volatility}%` : '12.4%'}
            </span>
          </div>

          <div className="ticker-item">
            <span className="ticker-label">HMM REGIME</span>
            <span className={`regime-tag ${regime?.currentRegime?.toLowerCase() || 'bull'}`}>
              {regime?.currentRegime || 'BULL_TREND'}
            </span>
          </div>

          <div className="ticker-item">
            <span className="ticker-label">IQ200 SIGNAL</span>
            <span className={`signal-tag ${liveData?.signal === 'BUY' ? 'tag-buy' : 'tag-sell'}`}>
              {liveData?.signal || 'BUY'}
            </span>
          </div>
        </header>

        {/* ==================================================== */}
        {/* TAB 1: OVERVIEW TERMINAL */}
        {/* ==================================================== */}
        {activeTab === 'overview' && (
          <div className="tab-pane">
            <div className="pane-header">
              <div>
                <h2>Portfolio Analytics & Executive Cockpit</h2>
                <p>Real-time dynamic allocation metrics across Nifty 50 and Nifty SmallCap 250</p>
              </div>
              <button onClick={handleLiveSync} disabled={isSyncing} className="btn-accent">
                <RefreshCw size={15} className={isSyncing ? 'animate-spin' : ''} />
                {isSyncing ? 'Synchronizing...' : 'Sync Market Feed'}
              </button>
            </div>

            {/* KPI METRICS ROW */}
            <div className="kpi-grid">
              <div className="card kpi-card">
                <div className="kpi-header">
                  <span>PORTFOLIO EQUITY</span>
                  <Activity size={16} className="text-cyan" />
                </div>
                <h2>₹{metrics.portfolioValue?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</h2>
                <span className="kpi-meta text-emerald">
                  <ArrowUpRight size={14} /> Initial ₹1,00,000 (100k Base)
                </span>
              </div>

              <div className="card kpi-card">
                <div className="kpi-header">
                  <span>TOTAL RETURN (CAGR)</span>
                  <TrendingUp size={16} className="text-emerald" />
                </div>
                <h2 className="text-emerald">+{metrics.totalReturn?.toFixed(1)}%</h2>
                <span className="kpi-meta">CAGR: <strong>{metrics.cagr}% p.a.</strong></span>
              </div>

              <div className="card kpi-card">
                <div className="kpi-header">
                  <span>SHARPE & SORTINO</span>
                  <Sliders size={16} className="text-cyan" />
                </div>
                <h2>{metrics.sharpeRatio} <span className="text-muted text-sm">/ {metrics.sortinoRatio}</span></h2>
                <span className="kpi-meta">Rf = 6.5% G-Sec benchmark</span>
              </div>

              <div className="card kpi-card">
                <div className="kpi-header">
                  <span>MAX DRAWDOWN</span>
                  <ShieldAlert size={16} className="text-rose" />
                </div>
                <h2 className="text-rose">{metrics.maxDrawdown}%</h2>
                <span className="kpi-meta">Calmar Ratio: <strong>{metrics.calmarRatio}</strong></span>
              </div>

              <div className="card kpi-card">
                <div className="kpi-header">
                  <span>WIN RATE & ALPHA</span>
                  <CheckCircle2 size={16} className="text-purple" />
                </div>
                <h2>{metrics.winRate}%</h2>
                <span className="kpi-meta">Alpha: <strong>+{metrics.alpha}%</strong> (Beta: {metrics.beta})</span>
              </div>
            </div>

            {/* CHARTS DUAL GRID */}
            <div className="charts-grid">
              <div className="card chart-panel">
                <div className="chart-header">
                  <div>
                    <h3>Cumulative Portfolio Trajectory</h3>
                    <p className="chart-sub">Performance comparison against underlying Nifty indices</p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={340}>
                  <LineChart data={chartData}>
                    <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="Date" stroke="#6b7280" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#6b7280" domain={['auto', 'auto']} tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`} tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff', borderRadius: '8px' }} />
                    <Legend />
                    <Line type="monotone" name="Portfolio (₹)" dataKey="Portfolio_Value" stroke="#00ffcc" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* IQ200 SIGNAL RADAR */}
              <div className="card side-panel">
                <div className="chart-header">
                  <h3>IQ200 Directional Signal</h3>
                  <span className="tag-model">XGBoost v2</span>
                </div>
                <div className="signal-hero">
                  <div className={`signal-circle ${iq200?.signal === 'BUY' ? 'glow-buy' : 'glow-sell'}`}>
                    <h2>{iq200?.signal || 'BUY'}</h2>
                    <span>{iq200?.confidence || 75}% CONFIDENCE</span>
                  </div>
                </div>
                <div className="signal-stats-grid">
                  <div className="signal-stat">
                    <span>Probability Up</span>
                    <strong>{iq200?.probability || 65}%</strong>
                  </div>
                  <div className="signal-stat">
                    <span>IQ Conviction</span>
                    <strong>{iq200?.iq_score || 50} / 100</strong>
                  </div>
                  <div className="signal-stat">
                    <span>Regime State</span>
                    <strong>{regime?.currentRegime || 'BULL_TREND'}</strong>
                  </div>
                  <div className="signal-stat">
                    <span>SMA 20/200 Ratio</span>
                    <strong>{regime?.smaRatio || 1.02}</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* TAB 2: MULTI-STRATEGY BACKTESTER */}
        {/* ==================================================== */}
        {activeTab === 'backtest' && backtestData && (
          <div className="tab-pane">
            <div className="pane-header">
              <div>
                <h2>Multi-Strategy Quantitative Backtester</h2>
                <p>Compare dynamic regime switching, risk parity, trend following, and index buy & hold</p>
              </div>
            </div>

            {/* STRATEGY TOGGLE BUTTONS */}
            <div className="strategy-toggle-bar">
              {Object.keys(selectedStrategies).map((strat) => (
                <button
                  key={strat}
                  className={`strat-toggle-btn ${selectedStrategies[strat] ? 'active' : ''}`}
                  style={{
                    borderColor: selectedStrategies[strat] ? strategyColors[strat] : '#374151',
                    color: selectedStrategies[strat] ? strategyColors[strat] : '#9ca3af'
                  }}
                  onClick={() =>
                    setSelectedStrategies(prev => ({ ...prev, [strat]: !prev[strat] }))
                  }
                >
                  <span className="dot" style={{ backgroundColor: strategyColors[strat] }}></span>
                  {strat}
                </button>
              ))}
            </div>

            {/* COMPARATIVE EQUITY CURVES */}
            <div className="card chart-panel" style={{ marginBottom: '24px' }}>
              <div className="chart-header">
                <h3>Comparative Equity Growth (Initial Capital: ₹1,00,000)</h3>
              </div>
              <ResponsiveContainer width="100%" height={380}>
                <LineChart data={backtestData.equityCurves}>
                  <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="Date" stroke="#6b7280" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#6b7280" domain={['auto', 'auto']} tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`} tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff', borderRadius: '8px' }} />
                  <Legend />
                  {selectedStrategies["Dynamic Regime"] && (
                    <Line type="monotone" name="Dynamic Regime" dataKey="Dynamic_Regime" stroke={strategyColors["Dynamic Regime"]} strokeWidth={2.5} dot={false} />
                  )}
                  {selectedStrategies["Risk Parity"] && (
                    <Line type="monotone" name="Risk Parity" dataKey="Risk_Parity" stroke={strategyColors["Risk Parity"]} strokeWidth={2} dot={false} />
                  )}
                  {selectedStrategies["Trend Following"] && (
                    <Line type="monotone" name="Trend Following" dataKey="Trend_Following" stroke={strategyColors["Trend Following"]} strokeWidth={2} dot={false} />
                  )}
                  {selectedStrategies["Static 50:50"] && (
                    <Line type="monotone" name="Static 50:50" dataKey="Static_50_50" stroke={strategyColors["Static 50:50"]} strokeWidth={2} strokeDasharray="4 4" dot={false} />
                  )}
                  {selectedStrategies["Nifty 50 Benchmark"] && (
                    <Line type="monotone" name="Nifty 50" dataKey="Nifty_50" stroke={strategyColors["Nifty 50 Benchmark"]} strokeWidth={1.8} dot={false} />
                  )}
                  {selectedStrategies["Smallcap 250 Benchmark"] && (
                    <Line type="monotone" name="Smallcap 250" dataKey="Smallcap_250" stroke={strategyColors["Smallcap 250 Benchmark"]} strokeWidth={1.8} dot={false} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* PERFORMANCE SCORECARD TABLE */}
            <div className="card table-container" style={{ marginBottom: '24px' }}>
              <div className="chart-header">
                <h3>Institutional Strategy Scorecard</h3>
              </div>
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Total Return</th>
                    <th>CAGR</th>
                    <th>Annual Vol</th>
                    <th>Sharpe (Rf=6.5%)</th>
                    <th>Sortino</th>
                    <th>Max Drawdown</th>
                    <th>Calmar</th>
                    <th>Win Rate</th>
                    <th>Profit Factor</th>
                    <th>Alpha</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(backtestData.scorecards || {}).map(([name, s]) => (
                    <tr key={name} className={name === 'Dynamic Regime' ? 'highlight-row' : ''}>
                      <td style={{ fontWeight: '600', color: strategyColors[name] || '#fff' }}>
                        {name}
                      </td>
                      <td className="text-emerald">+{s.totalReturn}%</td>
                      <td><strong>{s.cagr}%</strong></td>
                      <td>{s.annualVolatility}%</td>
                      <td><span className="badge-metric">{s.sharpeRatio}</span></td>
                      <td>{s.sortinoRatio}</td>
                      <td className="text-rose">{s.maxDrawdown}%</td>
                      <td>{s.calmarRatio}</td>
                      <td>{s.winRate}%</td>
                      <td>{s.profitFactor}</td>
                      <td className={s.alpha >= 0 ? 'text-emerald' : 'text-rose'}>
                        {s.alpha >= 0 ? `+${s.alpha}%` : `${s.alpha}%`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* UNDERWATER DRAWDOWN CURVE */}
            <div className="card chart-panel">
              <div className="chart-header">
                <h3>Underwater Drawdown Analysis (%)</h3>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={backtestData.drawdownCurves}>
                  <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="Date" stroke="#6b7280" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#6b7280" tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff', borderRadius: '8px' }} />
                  <Legend />
                  <Area type="monotone" name="Dynamic Strategy Drawdown" dataKey="Dynamic_Drawdown" stroke="#00ffcc" fill="#00ffcc" fillOpacity={0.25} />
                  <Area type="monotone" name="Nifty 50 Drawdown" dataKey="Benchmark_Drawdown" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* TAB 3: PORTFOLIO REBALANCER & TRADE TICKETS */}
        {/* ==================================================== */}
        {activeTab === 'rebalance' && rebalanceData && (
          <div className="tab-pane">
            <div className="pane-header">
              <div>
                <h2>Portfolio Rebalancing Assistant & Trade Execution Tickets</h2>
                <p>Calculates exact allocation drift and generates actionable buy/sell orders based on HMM state</p>
              </div>
              <button onClick={copyOrderTickets} className="btn-accent">
                {copiedTickets ? <Check size={16} /> : <Copy size={16} />}
                {copiedTickets ? 'Tickets Copied!' : 'Copy Trade Tickets'}
              </button>
            </div>

            <div className="terminal-layout">
              {/* REBALANCE CONTROLS */}
              <div className="terminal-sidebar">
                <div className="card control-box">
                  <h3>Capital & Holdings Setup</h3>

                  <div className="control-field">
                    <div className="flex-between">
                      <label>Total Portfolio Capital</label>
                      <strong className="text-cyan">₹{rebCapital.toLocaleString('en-IN')}</strong>
                    </div>
                    <input
                      type="range"
                      min="100000"
                      max="5000000"
                      step="50000"
                      value={rebCapital}
                      onChange={(e) => setRebCapital(Number(e.target.value))}
                      className="custom-slider"
                    />
                  </div>

                  <div className="control-field">
                    <div className="flex-between">
                      <label>Current Nifty 50 Split</label>
                      <strong className="text-purple">{currentNiftySplit}%</strong>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={currentNiftySplit}
                      onChange={(e) => setCurrentNiftySplit(Number(e.target.value))}
                      className="custom-slider"
                    />
                    <span className="kpi-meta">SmallCap 250: <strong>{100 - currentNiftySplit}%</strong></span>
                  </div>

                  <div className="rebalance-status-badge">
                    <span className={rebalanceData.needsRebalance ? 'badge-urgent' : 'badge-balanced'}>
                      {rebalanceData.needsRebalance ? '⚠️ REBALANCE RECOMMENDED' : '✓ PORTFOLIO OPTIMAL'}
                    </span>
                  </div>
                </div>

                <div className="card">
                  <div className="kpi-header">
                    <span>REGIME EXECUTION RATIONALE</span>
                    <ShieldCheck size={16} className="text-cyan" />
                  </div>
                  <p className="regime-desc" style={{ marginTop: '8px' }}>
                    {rebalanceData.regimeRationale}
                  </p>
                  <div style={{ marginTop: '12px', fontSize: '0.78rem', color: '#64748b' }}>
                    Estimated Frictions (STT + Brokerage): <strong className="text-white">₹{rebalanceData.estimatedFrictions}</strong>
                  </div>
                </div>
              </div>

              {/* REBALANCE TICKETS AND WEIGHT MATRIX */}
              <div className="terminal-main">
                {/* WEIGHT COMPARISON ROW */}
                <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', marginBottom: '20px' }}>
                  <div className="card">
                    <span className="ticker-label">CURRENT ALLOCATION</span>
                    <div style={{ display: 'flex', gap: '14px', marginTop: '10px' }}>
                      <div className="weight-box">
                        <span>Nifty 50</span>
                        <h3 className="text-white">{rebalanceData.currentWeights?.nifty}%</h3>
                        <p>₹{(rebCapital * ((rebalanceData.currentWeights?.nifty || 50) / 100)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                      </div>
                      <div className="weight-box">
                        <span>SmallCap 250</span>
                        <h3 className="text-purple">{rebalanceData.currentWeights?.smallcap}%</h3>
                        <p>₹{(rebCapital * ((rebalanceData.currentWeights?.smallcap || 50) / 100)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                      </div>
                    </div>
                  </div>

                  <div className="card" style={{ border: '1px solid rgba(0, 255, 204, 0.3)' }}>
                    <span className="ticker-label text-cyan">TARGET REGIME WEIGHTS</span>
                    <div style={{ display: 'flex', gap: '14px', marginTop: '10px' }}>
                      <div className="weight-box">
                        <span>Nifty 50</span>
                        <h3 className="text-cyan">{rebalanceData.targetWeights?.nifty}%</h3>
                        <p>₹{(rebCapital * ((rebalanceData.targetWeights?.nifty || 50) / 100)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                      </div>
                      <div className="weight-box">
                        <span>SmallCap 250</span>
                        <h3 className="text-cyan">{rebalanceData.targetWeights?.smallcap}%</h3>
                        <p>₹{(rebCapital * ((rebalanceData.targetWeights?.smallcap || 50) / 100)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* TRADE ORDER TICKETS TABLE */}
                <div className="card table-container">
                  <div className="chart-header">
                    <h3>Actionable Execution Order Sheet</h3>
                    <span className="tag-model">Live Pricing</span>
                  </div>
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Asset</th>
                        <th>Action</th>
                        <th>Delta Amount</th>
                        <th>Target Units</th>
                        <th>Current Weight</th>
                        <th>Target Weight</th>
                        <th>Drift %</th>
                        <th>Priority</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rebalanceData.orderTickets?.map((ticket, idx) => (
                        <tr key={idx} className={ticket.action !== 'HOLD' ? 'highlight-row' : ''}>
                          <td style={{ fontWeight: '600' }}>{ticket.asset}</td>
                          <td>
                            <span className={`signal-tag ${ticket.action === 'BUY' ? 'tag-buy' : ticket.action === 'SELL' ? 'tag-sell' : 'tag-model'}`}>
                              {ticket.action}
                            </span>
                          </td>
                          <td className="font-mono font-bold" style={{ color: ticket.action === 'BUY' ? '#00ffcc' : ticket.action === 'SELL' ? '#ef4444' : '#94a3b8' }}>
                            {ticket.action !== 'HOLD' ? `₹${ticket.amount?.toLocaleString('en-IN')}` : '--'}
                          </td>
                          <td className="font-mono">{ticket.units > 0 ? `${ticket.units} Units` : '--'}</td>
                          <td>{ticket.current_weight}%</td>
                          <td className="text-cyan font-bold">{ticket.target_weight}%</td>
                          <td className={ticket.drift > 0 ? 'text-emerald' : ticket.drift < 0 ? 'text-rose' : ''}>
                            {ticket.drift > 0 ? `+${ticket.drift}%` : `${ticket.drift}%`}
                          </td>
                          <td>
                            <span className={`badge-trend ${ticket.status === 'URGENT' ? 'trend-bear' : 'trend-bull'}`}>
                              {ticket.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* TAB 4: CRISIS STRESS-TESTER */}
        {/* ==================================================== */}
        {activeTab === 'stress' && stressData && (
          <div className="tab-pane">
            <div className="pane-header">
              <div>
                <h2>Historical Black Swan & Crisis Stress-Tester</h2>
                <p>Simulate portfolio survival, maximum stress drawdown, and capital recovery against market shocks</p>
              </div>
            </div>

            <div className="terminal-layout">
              {/* SCENARIO SELECTOR */}
              <div className="terminal-sidebar">
                <div className="card control-box">
                  <h3>Crisis Scenarios</h3>

                  <div className="control-field">
                    <label>Select Historical Crash</label>
                    <select
                      value={activeScenario}
                      onChange={(e) => setActiveScenario(e.target.value)}
                      className="custom-select"
                    >
                      <option value="COVID_2020">2020 COVID Flash Shock (-38% Nifty)</option>
                      <option value="GFC_2008">2008 Global Financial Crisis (-52% Nifty)</option>
                      <option value="RATE_HIKE_2022">2022 Inflation & Rate Hike (-18% Nifty)</option>
                      <option value="FLASH_CRASH">Intraday Flash Liquidity Squeeze (-12%)</option>
                      <option value="CUSTOM">Custom Black Swan Sandbox</option>
                    </select>
                  </div>

                  {activeScenario === 'CUSTOM' && (
                    <>
                      <div className="control-field">
                        <div className="flex-between">
                          <label>Nifty 50 Shock</label>
                          <strong className="text-rose">{customNiftyShock}%</strong>
                        </div>
                        <input
                          type="range"
                          min="-60"
                          max="-5"
                          value={customNiftyShock}
                          onChange={(e) => setCustomNiftyShock(Number(e.target.value))}
                          className="custom-slider"
                        />
                      </div>

                      <div className="control-field">
                        <div className="flex-between">
                          <label>SmallCap 250 Shock</label>
                          <strong className="text-rose">{customSmallcapShock}%</strong>
                        </div>
                        <input
                          type="range"
                          min="-70"
                          max="-5"
                          value={customSmallcapShock}
                          onChange={(e) => setCustomSmallcapShock(Number(e.target.value))}
                          className="custom-slider"
                        />
                      </div>

                      <div className="control-field">
                        <div className="flex-between">
                          <label>Volatility Multiplier</label>
                          <strong className="text-purple">{volMultiplier.toFixed(1)}x</strong>
                        </div>
                        <input
                          type="range"
                          min="1.0"
                          max="5.0"
                          step="0.2"
                          value={volMultiplier}
                          onChange={(e) => setVolMultiplier(Number(e.target.value))}
                          className="custom-slider"
                        />
                      </div>
                    </>
                  )}
                </div>

                {/* CRISIS SUMMARY CARDS */}
                <div className="card">
                  <div className="kpi-header">
                    <span>ALPHA PROTECTED (CRASH CUSHION)</span>
                    <ShieldCheck size={16} className="text-emerald" />
                  </div>
                  <h2 className="text-emerald" style={{ margin: '8px 0' }}>
                    +{stressData.alphaPreservedPct}%
                  </h2>
                  <p className="kpi-meta">Capital preservation vs unhedged Nifty</p>
                </div>

                <div className="card">
                  <div className="kpi-header">
                    <span>RECOVERY DURATION</span>
                    <TrendingUp size={16} className="text-cyan" />
                  </div>
                  <h3 className="text-white" style={{ margin: '6px 0' }}>
                    {stressData.estimatedRecoveryDays?.dynamicStrategy} Days
                  </h3>
                  <p className="kpi-meta">vs Nifty {stressData.estimatedRecoveryDays?.nifty50} Days | Smallcap {stressData.estimatedRecoveryDays?.smallcap250} Days</p>
                </div>
              </div>

              {/* STRESS TRAJECTORY AND COMPARISON */}
              <div className="terminal-main">
                {/* DRAWDOWN COMPARISON CARDS */}
                <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: '20px' }}>
                  <div className="card" style={{ border: '1px solid rgba(0, 255, 204, 0.3)' }}>
                    <span className="ticker-label text-cyan">DYNAMIC STRATEGY DRAWDOWN</span>
                    <h2 className="text-cyan">{stressData.drawdowns?.dynamicStrategy}%</h2>
                    <p className="kpi-meta">Projected Loss: ₹{stressData.capitalLosses?.dynamicStrategy?.toLocaleString('en-IN')}</p>
                  </div>

                  <div className="card">
                    <span className="ticker-label text-rose">NIFTY 50 BUY & HOLD</span>
                    <h2 className="text-rose">{stressData.drawdowns?.nifty50}%</h2>
                    <p className="kpi-meta">Projected Loss: ₹{stressData.capitalLosses?.nifty50?.toLocaleString('en-IN')}</p>
                  </div>

                  <div className="card">
                    <span className="ticker-label text-purple">SMALLCAP 250 BUY & HOLD</span>
                    <h2 className="text-purple">{stressData.drawdowns?.smallcap250}%</h2>
                    <p className="kpi-meta">Projected Loss: ₹{stressData.capitalLosses?.smallcap250?.toLocaleString('en-IN')}</p>
                  </div>
                </div>

                {/* CRISIS TRAJECTORY CONE */}
                <div className="card chart-panel">
                  <div className="chart-header">
                    <div>
                      <h3>{stressData.scenario} — Capital Trajectory</h3>
                      <p className="chart-sub">{stressData.description}</p>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={stressData.trajectory}>
                      <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="day" stroke="#6b7280" tick={{ fontSize: 11 }} />
                      <YAxis stroke="#6b7280" domain={['auto', 'auto']} tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff', borderRadius: '8px' }} />
                      <Legend />
                      <Line type="monotone" name="Dynamic Strategy" dataKey="Dynamic_Strategy" stroke="#00ffcc" strokeWidth={2.8} dot={false} />
                      <Line type="monotone" name="Static 50:50" dataKey="Static_50_50" stroke="#a855f7" strokeWidth={1.8} strokeDasharray="4 4" dot={false} />
                      <Line type="monotone" name="Nifty 50 Index" dataKey="Nifty_50" stroke="#ef4444" strokeWidth={2} dot={false} />
                      <Line type="monotone" name="SmallCap 250 Index" dataKey="Smallcap_250" stroke="#f97316" strokeWidth={1.8} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* TAB 3: MONTE CARLO & VAR TERMINAL */}
        {/* ==================================================== */}
        {activeTab === 'forecast' && (
          <div className="tab-pane">
            <div className="pane-header">
              <div>
                <h2>Monte Carlo Risk Simulation & Value-at-Risk (VaR)</h2>
                <p>200-path stochastic forecast with ML drift calibration and tail-risk analysis</p>
              </div>
            </div>

            <div className="terminal-layout">
              {/* PARAMETER CONTROL PANEL */}
              <div className="terminal-sidebar">
                <div className="card control-box">
                  <h3>Simulation Parameters</h3>

                  <div className="control-field">
                    <label>Drift Model</label>
                    <select
                      value={activeModel}
                      onChange={(e) => setActiveModel(e.target.value)}
                      className="custom-select"
                    >
                      <option value="Ensemble">XGBoost + Technical Drift</option>
                      <option value="Historical">Historical Drift (Empirical)</option>
                      <option value="Conservative">Zero Drift (Stress Test)</option>
                    </select>
                  </div>

                  <div className="control-field">
                    <div className="flex-between">
                      <label>Forecast Horizon</label>
                      <strong className="text-cyan">{horizon} Days</strong>
                    </div>
                    <input
                      type="range"
                      min="7"
                      max="90"
                      value={horizon}
                      onChange={(e) => setHorizon(Number(e.target.value))}
                      className="custom-slider"
                    />
                  </div>

                  <div className="control-field">
                    <div className="flex-between">
                      <label>Volatility Scaling</label>
                      <strong className="text-purple">{volatility.toFixed(1)}x</strong>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="3.0"
                      step="0.1"
                      value={volatility}
                      onChange={(e) => setVolatility(Number(e.target.value))}
                      className="custom-slider"
                    />
                  </div>
                </div>

                {/* VAR RISK CARDS */}
                <div className="card risk-card">
                  <div className="kpi-header">
                    <span>95% VALUE-AT-RISK (VaR)</span>
                    <ShieldAlert size={16} className="text-rose" />
                  </div>
                  <h3 className="text-rose">₹{simData.VaR95?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</h3>
                  <p className="kpi-meta">5% worst-case terminal threshold</p>
                </div>

                <div className="card risk-card">
                  <div className="kpi-header">
                    <span>95% EXPECTED SHORTFALL (CVaR)</span>
                    <ShieldAlert size={16} className="text-rose" />
                  </div>
                  <h3 className="text-rose">₹{simData.CVaR95?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</h3>
                  <p className="kpi-meta">Average tail loss beyond 95% VaR</p>
                </div>

                <div className="card">
                  <h4>Probability of Positive Gain</h4>
                  <h2 style={{ color: simData.probPositive >= 50 ? '#00ffcc' : '#ef4444', margin: '8px 0' }}>
                    {simData.probPositive}%
                  </h2>
                  <div className="progress-track">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${simData.probPositive}%`,
                        backgroundColor: simData.probPositive >= 50 ? '#00ffcc' : '#ef4444'
                      }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* MONTE CARLO VISUALIZATIONS */}
              <div className="terminal-main">
                <div className="card chart-panel" style={{ marginBottom: '20px' }}>
                  <div className="chart-header">
                    <div>
                      <h3>Monte Carlo Confidence Cone ({horizon} Days)</h3>
                      <p className="chart-sub">Median path with 5th to 95th percentile confidence bands</p>
                    </div>
                    <div className="forecast-summary-pills">
                      <span>Worst: <strong className="text-rose">₹{simData.worstCase?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</strong></span>
                      <span>Target: <strong className="text-cyan">₹{simData.targetValue?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</strong></span>
                      <span>Best: <strong className="text-emerald">₹{simData.bestCase?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</strong></span>
                    </div>
                  </div>

                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={simData.chartData}>
                      <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="day" stroke="#6b7280" tick={{ fontSize: 11 }} />
                      <YAxis stroke="#6b7280" tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff', borderRadius: '8px' }} />
                      {Array.from({ length: 12 }).map((_, i) => (
                        <Line
                          key={i}
                          type="monotone"
                          dataKey={`path_${i}`}
                          stroke="#00ffcc"
                          strokeWidth={1}
                          opacity={0.12}
                          dot={false}
                          isAnimationActive={false}
                        />
                      ))}
                      <Line type="monotone" name="5th Percentile" dataKey="p5" stroke="#ef4444" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
                      <Line type="monotone" name="95th Percentile" dataKey="p95" stroke="#10b981" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
                      <Line type="monotone" name="Expected Target" dataKey="Target" stroke="#00ffcc" strokeWidth={2.8} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* FEATURE IMPORTANCES */}
                <div className="card chart-panel">
                  <div className="chart-header">
                    <h3>Predictive Feature Importance (XGBoost)</h3>
                    <span className="tag-model">SHAP Contribution</span>
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={simData.shapData} layout="vertical" margin={{ left: 50, right: 30, top: 10, bottom: 10 }}>
                      <CartesianGrid stroke="#1f2937" horizontal={false} strokeDasharray="3 3" />
                      <XAxis type="number" stroke="#6b7280" tick={{ fontSize: 11 }} />
                      <YAxis dataKey="feature" type="category" stroke="#6b7280" tick={{ fontSize: 11 }} width={120} />
                      <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff', borderRadius: '8px' }} />
                      <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                        {simData.shapData?.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill || '#00ffcc'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================================================== */}
        {/* TAB 4: HMM REGIME DIAGNOSTICS */}
        {/* ==================================================== */}
        {activeTab === 'regime' && (
          <div className="tab-pane">
            <div className="pane-header">
              <div>
                <h2>Gaussian Hidden Markov Model (HMM) Regime Matrix</h2>
                <p>3-state statistical regime classification based on empirical drift and return volatility</p>
              </div>
            </div>

            <div className="regime-grid">
              <div className="card regime-summary-card">
                <h3>Current Market Regime</h3>
                <div className={`regime-badge-lg ${regime?.currentRegime?.toLowerCase() || 'bull'}`}>
                  {regime?.currentRegime || 'BULL_TREND'}
                </div>
                <p className="regime-desc">
                  {regime?.currentRegime === 'BULL_TREND' && 'High positive momentum, sustained trend strength, and low-to-moderate volatility.'}
                  {regime?.currentRegime === 'BEAR_MARKET' && 'Elevated volatility, negative drift, and high probability of drawdowns.'}
                  {regime?.currentRegime === 'SIDEWAYS_VOLATILE' && 'Consolidation phase with range-bound oscillations and fluctuating momentum.'}
                </p>

                <div className="regime-probs-list">
                  <h4>State Posterior Probabilities</h4>
                  {Object.entries(regime?.probabilities || {}).map(([k, v]) => (
                    <div key={k} className="prob-row">
                      <span>{k}</span>
                      <div className="prob-bar-container">
                        <div className="prob-bar" style={{ width: `${v}%`, backgroundColor: k.includes('BULL') ? '#00ffcc' : k.includes('BEAR') ? '#ef4444' : '#eab308' }}></div>
                      </div>
                      <strong>{v}%</strong>
                    </div>
                  ))}
                </div>
              </div>

              {/* MARKOV TRANSITION MATRIX */}
              <div className="card">
                <h3>Markov Transition Probability Matrix</h3>
                <p className="chart-sub">Likelihood of switching between states on the next trading session</p>

                <div className="matrix-display">
                  <div className="matrix-row header-row">
                    <span>From \ To</span>
                    <span>Bull State</span>
                    <span>Volatile State</span>
                    <span>Bear State</span>
                  </div>
                  {(regime?.transmat || [[0.98, 0.01, 0.01], [0.02, 0.97, 0.01], [0.02, 0.02, 0.96]]).map((row, i) => (
                    <div key={i} className="matrix-row">
                      <span className="state-name">{i === 0 ? 'Bull State' : i === 1 ? 'Volatile State' : 'Bear State'}</span>
                      {row.map((val, j) => (
                        <span key={j} className="matrix-cell" style={{ backgroundColor: `rgba(0, 255, 204, ${Math.min(val, 1) * 0.45})` }}>
                          {(val * 100).toFixed(1)}%
                        </span>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* HISTORICAL REGIME CLASSIFICATION TIMELINE */}
            {regimeHistory && regimeHistory.length > 0 && (
              <div className="card chart-panel" style={{ marginTop: '24px' }}>
                <div className="chart-header">
                  <h3>Historical Regime Classifications (Last 180 Sessions)</h3>
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={regimeHistory}>
                    <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#6b7280" domain={['auto', 'auto']} tickFormatter={(v) => Number(v).toFixed(0)} tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff', borderRadius: '8px' }} />
                    <Line type="monotone" name="Nifty 50 Close" dataKey="nifty" stroke="#38bdf8" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* ==================================================== */}
        {/* TAB 5: QUANTITATIVE LEDGER & DATA MATRIX */}
        {/* ==================================================== */}
        {activeTab === 'data' && (
          <div className="tab-pane">
            <div className="pane-header">
              <div>
                <h2>Nifty 50 & SmallCap 250 Technical Ledger</h2>
                <p>Complete historical database with mathematical indicators and signals</p>
              </div>
              <div className="action-buttons">
                <button
                  onClick={() => window.open(`${API_BASE_URL}/api/download-report`, '_blank')}
                  className="btn-outline"
                >
                  <FileSpreadsheet size={15} />
                  Export Excel Report
                </button>
                <button onClick={handleLiveSync} disabled={isSyncing} className="btn-accent">
                  <RefreshCw size={15} className={isSyncing ? 'animate-spin' : ''} />
                  {isSyncing ? 'Syncing...' : 'Sync Market Feed'}
                </button>
              </div>
            </div>

            {/* SEARCH / FILTER INPUT */}
            <div className="table-search-bar">
              <input
                type="text"
                placeholder="Search by date (YYYY-MM-DD) or trend (Bullish/Bearish)..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="search-input"
              />
              <span className="row-count-badge">
                Showing {filteredTableData.length} records
              </span>
            </div>

            <div className="card table-container">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Nifty 50</th>
                    <th>SmallCap 250</th>
                    <th>Ratio</th>
                    <th>1W Ret</th>
                    <th>1M Ret</th>
                    <th>1Y Ret</th>
                    <th>20 SMA</th>
                    <th>200 SMA</th>
                    <th>SMA Trend</th>
                    <th>14D RSI</th>
                    <th>MACD</th>
                    <th>BB Upper</th>
                    <th>BB Lower</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTableData.slice(0, 100).map((row, idx) => (
                    <tr key={idx}>
                      <td className="text-muted font-mono">{row.Date || 'N/A'}</td>
                      <td className="text-white font-semibold">
                        ₹{Number(row.Nifty50 || 0).toLocaleString('en-IN', { maximumFractionDigits: 1 })}
                      </td>
                      <td className="text-purple">
                        {Number(row.Smallcap250 || 0).toLocaleString('en-IN', { maximumFractionDigits: 1 })}
                      </td>
                      <td className="text-muted">
                        {row.Ratio ? Number(row.Ratio).toFixed(3) : '--'}
                      </td>
                      <td className={row.Nifty_1W_Return >= 0 ? 'text-emerald' : 'text-rose'}>
                        {row.Nifty_1W_Return ? `${(row.Nifty_1W_Return * 100).toFixed(2)}%` : '0.00%'}
                      </td>
                      <td className={row.Nifty_1M_Return >= 0 ? 'text-emerald' : 'text-rose'}>
                        {row.Nifty_1M_Return ? `${(row.Nifty_1M_Return * 100).toFixed(2)}%` : '0.00%'}
                      </td>
                      <td className={row.Nifty_1Y_Return >= 0 ? 'text-emerald' : 'text-rose'}>
                        {row.Nifty_1Y_Return ? `${(row.Nifty_1Y_Return * 100).toFixed(2)}%` : '0.00%'}
                      </td>
                      <td>{Number(row.Nifty_20_SMA || 0).toFixed(0)}</td>
                      <td>{Number(row.Nifty_200_SMA || 0).toFixed(0)}</td>
                      <td>
                        <span className={`badge-trend ${row.SMA_Trend === 'Bullish' ? 'trend-bull' : 'trend-bear'}`}>
                          {row.SMA_Trend || 'Bullish'}
                        </span>
                      </td>
                      <td className={row.Nifty_RSI >= 70 ? 'text-rose font-bold' : row.Nifty_RSI <= 30 ? 'text-emerald font-bold' : 'text-white'}>
                        {row.Nifty_RSI ? Number(row.Nifty_RSI).toFixed(1) : '50.0'}
                      </td>
                      <td>{row.MACD ? Number(row.MACD).toFixed(1) : '0.0'}</td>
                      <td className="text-muted">{Number(row.BB_Upper || 0).toFixed(0)}</td>
                      <td className="text-muted">{Number(row.BB_Lower || 0).toFixed(0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;