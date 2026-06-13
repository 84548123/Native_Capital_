// src/App.jsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { LayoutDashboard, TrendingUp, Database, Activity, RefreshCw, FileSpreadsheet, Radio, Brain, ShieldAlert } from 'lucide-react';
import './App.css';

// Dynamically handle local testing vs Cloudflare tunneling
const isLocal = window.location.hostname === "localhost";
const API_BASE_URL = isLocal ? "https://native-capital.onrender.com" : "https://native-capital.onrender.com";
const WS_BASE_URL = isLocal ?   "wss://native-capital.onrender.com/ws/ledger" : "wss://native-capital.onrender.com/ws/ledger";

function App() {
  const [activeTab, setActiveTab] = useState('forecast'); 
  const [metrics, setMetrics] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [tableData, setTableData] = useState([]); 
  const [isSyncing, setIsSyncing] = useState(false);
  
  // Forecast State Variables
  const [simData, setSimData] = useState(null);
  const [horizon, setHorizon] = useState(7); 
  const [volatility, setVolatility] = useState(1.0);
  const [activeModel, setActiveModel] = useState('Ensemble Consensus');

  // Live WebSocket & Analytics States
  const [liveData, setLiveData] = useState(null);
  const [streamConnected, setStreamConnected] = useState(false);
  const [iq200, setIq200] = useState(null);
  const [regime, setRegime] = useState(null);

  // 1. Initial HTTP Data Load
  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/metrics`).then(res => res.json()),
      fetch(`${API_BASE_URL}/api/historical-data`).then(res => res.json()),
      fetch(`${API_BASE_URL}/api/raw-data`).then(res => res.json()),
      fetch(`${API_BASE_URL}/api/iq200`).then(res => res.json()),
      fetch(`${API_BASE_URL}/api/regime`).then(res => res.json()) 
    ])
    .then(([metricsJson, chartJson, tableJson, iq200Json, regimeJson]) => {
      setMetrics(metricsJson);
      setChartData(chartJson);
      setTableData(tableJson);
      setIq200(iq200Json); 
      setRegime(regimeJson);

      // PRE-FILL LIVE DATA: Instantly load the ticker bar before the WebSocket connects
      if (tableJson && tableJson.length > 0) {
        const latestRow = tableJson[0];
        setLiveData({
          nifty50: Number(latestRow.Nifty50),
          rsi: Number(latestRow.Nifty_RSI).toFixed(1),
          volatility: regimeJson?.volatility ? (Number(regimeJson.volatility) * 100).toFixed(2) : 12.4,
          signal: latestRow.SMA_Trend === "Bullish" ? "BUY" : "SELL"
        });
      }
    })
    .catch(err => console.error("API Engine Payload Matrix Error:", err));
  }, []);

  // 2. HTTP Simulation Engine Hook
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/simulate?horizon=${horizon}&vol=${volatility}&model=${activeModel}`)
      .then(res => res.json())
      .then(data => setSimData(data))
      .catch(err => console.error("Sim Error:", err));
  }, [horizon, volatility, activeModel]);

  // 3. Persistent Live WebSocket Hook
  useEffect(() => {
    let socket = new WebSocket(WS_BASE_URL);

    const connectSocket = () => {
      socket.onopen = () => setStreamConnected(true);
      
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === "MARKET_UPDATE") {
            setLiveData(payload.metrics);
          }
        } catch (error) {
          console.error("Stream parsing error:", error);
        }
      };

      socket.onclose = () => {
        setStreamConnected(false);
        setTimeout(() => connectSocket(), 3000); 
      };
    };

    connectSocket();
    return () => socket.close();
  }, []);

  const handleLiveSync = () => {
    setIsSyncing(true);
    fetch(`${API_BASE_URL}/api/sync-market`)
      .then(res => res.json())
      .then(data => {
        alert(data.message);
        if(data.status === "success") window.location.reload(); 
      })
      .catch(err => alert("Failed to connect to market data."))
      .finally(() => setIsSyncing(false));
  };

  if (!metrics || !simData) return <div className="loading">Initializing Quant Engine...</div>;

  return (
    <div className="app-container">
      {/* SIDEBAR NAVIGATION */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Activity color="#00ffcc" size={28} />
          <h2>Native Capital</h2>
        </div>
        <nav className="sidebar-nav">
          <button className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
            <LayoutDashboard size={20} /><span>Overview</span>
          </button>
          <button className={`nav-item ${activeTab === 'forecast' ? 'active' : ''}`} onClick={() => setActiveTab('forecast')}>
            <TrendingUp size={20} /><span>Forecast Terminal</span>
          </button>
          <button className={`nav-item ${activeTab === 'data' ? 'active' : ''}`} onClick={() => setActiveTab('data')}>
            <Database size={20} /><span>Quant Ledger</span>
          </button>
        </nav>

        {/* WEBSOCKET STATUS INDICATOR */}
        <div style={{ marginTop: 'auto', padding: '20px', borderTop: '1px solid #2A2E39' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: streamConnected ? '#00ffcc' : '#ff4444', fontSize: '0.85rem', fontWeight: 'bold' }}>
            <Radio size={16} className={streamConnected ? 'pulse-anim' : ''} />
            {streamConnected ? 'LIVE FEED CONNECTED' : 'FEED DISCONNECTED'}
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="main-content">

        {/* GLOBAL LIVE TICKER BAR (Now persistently renders) */}
        <div style={{ display: 'flex', justifyContent: 'space-between', backgroundColor: '#1E222D', padding: '12px 24px', borderRadius: '8px', marginBottom: '20px', border: '1px solid #2A2E39' }}>
          <span style={{color: '#858D99', fontSize: '0.9rem'}}>NIFTY 50 LIVE: <strong style={{color: '#fff', fontSize: '1.1rem', marginLeft: '8px'}}>{liveData ? liveData.nifty50.toLocaleString('en-IN', {minimumFractionDigits: 2}) : 'SYNCING...'}</strong></span>
          <span style={{color: '#858D99', fontSize: '0.9rem'}}>RSI (14): <strong style={{color: '#00ffcc', fontSize: '1.1rem', marginLeft: '8px'}}>{liveData ? liveData.rsi : '--'}</strong></span>
          <span style={{color: '#858D99', fontSize: '0.9rem'}}>MARKET VOLATILITY: <strong style={{color: '#ff00ff', fontSize: '1.1rem', marginLeft: '8px'}}>{liveData ? `${liveData.volatility}%` : '--'}</strong></span>
          <span style={{color: '#858D99', fontSize: '0.9rem'}}>ACTIVE SIGNAL: <strong style={{color: liveData?.signal?.includes('BUY') ? '#00ffcc' : liveData?.signal?.includes('SELL') ? '#ff4444' : '#ff00ff', fontSize: '1.1rem', marginLeft: '8px'}}>{liveData ? liveData.signal : 'WAIT'}</strong></span>
        </div>
        
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="dashboard-view">
            <h2 className="page-title">📊 Portfolio Overview</h2>
            <div className="kpi-grid">
              <div className="card">
                <h4>Portfolio Value</h4>
                <h2>₹{metrics.portfolioValue?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</h2>
              </div>
              <div className="card">
                <h4>Total Return</h4>
                <h2 className="positive-text">+{metrics.totalReturn?.toFixed(2)}%</h2>
              </div>
              <div className="card">
                <h4>Sharpe Ratio</h4>
                <h2>{metrics.sharpeRatio}</h2>
              </div>
            </div>
            <div className="chart-container">
              <h3>Historical Growth Curve</h3>
              <ResponsiveContainer width="100%" height={450}>
                <LineChart data={chartData}>
                  <CartesianGrid stroke="#2A2E39" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="Date" stroke="#858D99" />
                  <YAxis stroke="#858D99" domain={['auto', 'auto']} tickFormatter={(val) => `₹${(val/100000).toFixed(1)}L`} />
                  <Tooltip contentStyle={{ backgroundColor: '#1E222D', borderColor: '#2A2E39', color: '#fff' }} />
                  <Line type="monotone" dataKey="Portfolio_Value" stroke="#00ffcc" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* HIGH DENSITY FORECAST TERMINAL TAB */}
        {activeTab === 'forecast' && (
          <div className="dashboard-view">
            <h2 className="page-title" style={{marginBottom: '15px'}}>🔮 Forecast & Risk Terminal</h2>
            <div className="terminal-grid">
              
              {/* LEFT COLUMN: CONTROLS & KPIS */}
              <div className="terminal-left-pane">
                <div className="control-panel card">
                  <h3 style={{margin: '0 0 15px 0', fontSize: '1rem', color: '#fff'}}>Simulation Parameters</h3>
                  <div className="control-group">
                    <label>Engine Framework</label>
                    <select value={activeModel} onChange={(e) => setActiveModel(e.target.value)} className="modern-input">
                      <option value="Ensemble Consensus">Ensemble Consensus</option>
                      <option value="XGBoost (Tabular)">XGBoost (Tabular)</option>
                      <option value="LSTM (Sequence)">LSTM (Sequence)</option>
                    </select>
                  </div>
                  <div className="control-group">
                    <label>Horizon: <strong>{horizon} Days</strong></label>
                    <input type="range" min="7" max="60" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} className="modern-slider" />
                  </div>
                  <div className="control-group">
                    <label>Volatility: <strong>{volatility.toFixed(1)}x</strong></label>
                    <input type="range" min="0.5" max="3.0" step="0.1" value={volatility} onChange={(e) => setVolatility(Number(e.target.value))} className="modern-slider" />
                  </div>
                </div>

                <div className="card signal-card">
                  <h4>IQ200 Signal</h4>
                  <div
                    className="signal-badge"
                    style={{
                      backgroundColor: iq200?.signal === "BUY" ? "#052d20" : "#3a1010",
                      color: iq200?.signal === "BUY" ? "#00ffcc" : "#ff4444"
                    }}
                  >
                    {iq200?.signal || "WAIT"}
                  </div>
                  <p style={{ marginTop: "10px" }}>
                    Confidence: <strong> {iq200?.confidence || 0}%</strong>
                  </p>
                </div>     

                <div className="card">
                  <h4>IQ200 Score</h4>
                  <h2 style={{ color: iq200?.iq_score >= 60 ? "#00ffcc" : "#ff4444" }}>
                    {iq200?.iq_score || 0}
                  </h2>
                  <p>Probability Up: {" "}{(iq200?.probability || 0).toFixed(2)}%</p>
                </div>

                <div className="card">
                  <h4>Market Regime</h4>
                  <h2 style={{ color: regime?.currentRegime === "BULL" ? "#00ffcc" : "#ff4444" }}>
                    {regime?.currentRegime || "UNKNOWN"}
                  </h2>
                  <p>SMA20: {" "}{regime?.sma20?.toFixed(0) || "N/A"}</p>
                  <p>SMA200: {" "}{regime?.sma200?.toFixed(0) || "N/A"}</p>
                </div>

                <div className="card">
                  <h4>Prob. of Positive Return</h4>
                  <h2 style={{color: simData.probPositive > 50 ? '#00ffcc' : '#ff4444', margin: '5px 0'}}>{simData.probPositive}%</h2>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{width: `${simData.probPositive}%`, backgroundColor: simData.probPositive > 50 ? '#00ffcc' : '#ff4444'}}></div>
                  </div>
                </div>
              </div>

              {/* RIGHT COLUMN: DATA VISUALIZATION */}
              <div className="terminal-right-pane">
                <div className="chart-container terminal-main-chart">
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px'}}>
                    <h3 style={{margin: 0}}>Monte Carlo Confidence Cone</h3>
                    <div style={{fontSize: '0.85rem', color: '#858D99', display: 'flex', gap: '15px'}}>
                      <span>Worst: <strong className="negative-text">₹{simData.worstCase?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</strong></span>
                      <span>Target: <strong style={{color: '#ff00ff'}}>₹{simData.targetValue?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</strong></span>
                      <span>Best: <strong className="positive-text">₹{simData.bestCase?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</strong></span>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height="90%">
                    <LineChart data={simData.chartData}>
                      <CartesianGrid stroke="#2A2E39" strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="day" stroke="#858D99" tick={{fontSize: 12}} />
                      <YAxis stroke="#858D99" domain={['auto', 'auto']} tickFormatter={(val) => `₹${(val/100000).toFixed(1)}L`} tick={{fontSize: 12}} width={50} />
                      <Tooltip contentStyle={{ backgroundColor: '#1E222D', borderColor: '#2A2E39', color: '#fff' }} />
                      {Array.from({ length: 25 }).map((_, i) => (
                        <Line key={i} type="monotone" dataKey={`path_${i}`} stroke="#00ffcc" strokeWidth={1} opacity={0.15} dot={false} isAnimationActive={false} />
                      ))}
                      <Line type="monotone" dataKey="Target" stroke="#ff00ff" strokeWidth={3} strokeDasharray="5 5" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="chart-container terminal-sub-chart">
                  <h3 style={{margin: '0 0 10px 0'}}>Attribute Vectors (SHAP Impact)</h3>
                  <ResponsiveContainer width="100%" height="85%">
                    <BarChart data={simData.shapData} layout="vertical" margin={{ top: 0, right: 20, left: 30, bottom: 0 }}>
                      <CartesianGrid stroke="#2A2E39" horizontal={false} strokeDasharray="3 3" />
                      <XAxis type="number" stroke="#858D99" tick={{fontSize: 12}} />
                      <YAxis dataKey="feature" type="category" stroke="#858D99" width={110} tick={{fontSize: 12}} />
                      <Tooltip cursor={{fill: '#1E222D'}} contentStyle={{ backgroundColor: '#1E222D', borderColor: '#2A2E39', color: '#fff' }} />
                      <Bar dataKey="impact" radius={[0, 4, 4, 0]} barSize={20}>
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

        {/* RAW DATA TAB */}
        {activeTab === 'data' && (
          <div className="dashboard-view">
             <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px'}}>
              <h2 className="page-title" style={{margin: 0}}>🗄️ Nifty 50 Quant Ledger Engine</h2>
              <div style={{display: 'flex', gap: '12px'}}>
                <button onClick={() => window.open(`${API_BASE_URL}/api/download-report`, '_blank')} className="btn-secondary">
                  <FileSpreadsheet size={16} /> Download Excel Report
                </button>
                <button onClick={handleLiveSync} disabled={isSyncing} className={`btn-primary ${isSyncing ? 'syncing' : ''}`}>
                  <RefreshCw size={16} className={isSyncing ? 'animate-spin' : ''} />
                  {isSyncing ? 'Syncing Engine...' : '⚡ Fetch Live Market Data'}
                </button>
              </div>
            </div>
            
            <div className="card table-container" style={{overflowX: 'auto'}}>
              {tableData.length === 0 ? (
                <p style={{color: '#858D99', textAlign: 'center', padding: '20px'}}>No records found.</p>
              ) : (
                <table style={{width: '100%', borderCollapse: 'collapse', color: '#fff', textAlign: 'left', minWidth: '1400px'}}>
                  <thead>
                    <tr style={{borderBottom: '2px solid #2A2E39', color: '#858D99', fontSize: '12px', whiteSpace: 'nowrap'}}>
                      <th style={{padding: '12px'}}>Date</th>
                      <th style={{padding: '12px'}}>Nifty 50 Spot</th>
                      <th style={{padding: '12px'}}>1W Ret</th>
                      <th style={{padding: '12px'}}>1M Ret</th>
                      <th style={{padding: '12px'}}>1Y Ret</th>
                      <th style={{padding: '12px'}}>20 SMA</th>
                      <th style={{padding: '12px'}}>50 SMA</th>
                      <th style={{padding: '12px'}}>200 SMA</th>
                      <th style={{padding: '12px'}}>SMA Trend</th>
                      <th style={{padding: '12px'}}>20/200 Ratio</th>
                      <th style={{padding: '12px'}}>50 EMA</th>
                      <th style={{padding: '12px'}}>200 EMA</th>
                      <th style={{padding: '12px'}}>RSI (14D)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.map((row, index) => (
                      <tr key={index} style={{borderBottom: '1px solid #1E222D', fontSize: '13px', whiteSpace: 'nowrap'}}>
                        <td style={{padding: '12px', fontWeight: '600', color: '#858D99'}}>{row.Date || 'N/A'}</td>
                        <td style={{padding: '12px', color: '#ff00ff', fontWeight: '600'}}>{row.Nifty50 ? Number(row.Nifty50).toLocaleString('en-IN', { maximumFractionDigits: 1 }) : 'N/A'}</td>
                        
                        <td style={{padding: '12px', color: row.Nifty_1W_Return >= 0 ? '#00ffcc' : '#ff4444'}}>{row.Nifty_1W_Return !== undefined ? `${(row.Nifty_1W_Return * 100).toFixed(2)}%` : '0.00%'}</td>
                        <td style={{padding: '12px', color: row.Nifty_1M_Return >= 0 ? '#00ffcc' : '#ff4444'}}>{row.Nifty_1M_Return !== undefined ? `${(row.Nifty_1M_Return * 100).toFixed(2)}%` : '0.00%'}</td>
                        <td style={{padding: '12px', color: row.Nifty_1Y_Return >= 0 ? '#00ffcc' : '#ff4444'}}>{row.Nifty_1Y_Return !== undefined ? `${(row.Nifty_1Y_Return * 100).toFixed(2)}%` : '0.00%'}</td>
                        
                        <td style={{padding: '12px', color: '#e2e8f0'}}>{row.Nifty_20_SMA ? Number(row.Nifty_20_SMA).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : 'N/A'}</td>
                        <td style={{padding: '12px', color: '#cbd5e1'}}>{row.Nifty_50_SMA ? Number(row.Nifty_50_SMA).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : 'N/A'}</td>
                        <td style={{padding: '12px', color: '#94a3b8'}}>{row.Nifty_200_SMA ? Number(row.Nifty_200_SMA).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : 'N/A'}</td>
                        
                        <td style={{padding: '12px', fontWeight: 'bold', color: row.SMA_Trend === 'Bullish' ? '#00ffcc' : '#ff4444'}}>{row.SMA_Trend || 'N/A'}</td>
                        <td style={{padding: '12px', color: '#cbd5e1'}}>{row.SMA_20_200_Ratio ? Number(row.SMA_20_200_Ratio).toFixed(3) : 'N/A'}</td>
                        
                        <td style={{padding: '12px', color: '#334155'}}>{row.Nifty_50_EMA ? Number(row.Nifty_50_EMA).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : 'N/A'}</td>
                        <td style={{padding: '12px', color: '#1e293b'}}>{row.Nifty_200_EMA ? Number(row.Nifty_200_EMA).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : 'N/A'}</td>
                        <td style={{padding: '12px', fontWeight: '700', color: row.Nifty_RSI >= 70 ? '#ff4444' : row.Nifty_RSI <= 30 ? '#00ffcc' : '#fff'}}>
                          {row.Nifty_RSI ? Number(row.Nifty_RSI).toFixed(1) : '50.0'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default App;