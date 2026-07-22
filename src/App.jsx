import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, DollarSign, Clock, Layers, ChevronDown, ChevronRight, X, ListTree } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [summary, setSummary] = useState(null);
  const [calls, setCalls] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [selectedEnv, setSelectedEnv] = useState("");
  const [activeSession, setActiveSession] = useState(null);
  const [sessionCalls, setSessionCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  const viewSessionTrace = async (sessionId) => {
    try {
      const res = await axios.get(`${API_BASE}/api/v1/analytics/sessions/${sessionId}`);
      setSessionCalls(res.data);
      setActiveSession(sessionId);
    } catch (err) {
      console.error("Error fetching session:", err);
      alert("Session not found or error loading trace.");
    }
  };

  const toggleRow = (id) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = selectedEnv ? { env: selectedEnv } : {};
        const [summaryRes, callsRes, anomaliesRes] = await Promise.all([
          axios.get(`${API_BASE}/api/v1/analytics/summary`, { params }),
          axios.get(`${API_BASE}/api/v1/calls`, { params }),
          axios.get(`${API_BASE}/api/v1/analytics/anomalies`, { params })
        ]);
        setSummary(summaryRes.data);
        setCalls(callsRes.data);
        setAnomalies(anomaliesRes.data);
      } catch (err) {
        console.error("Error fetching data:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    // Auto refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [selectedEnv]);

  if (loading && !summary) {
    return <div className="min-h-screen flex items-center justify-center">Loading Telemetry...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-900 p-8 text-slate-100 font-sans">
      <header className="mb-8 border-b border-slate-700 pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-blue-400 flex items-center gap-2">
            <Activity className="w-8 h-8" />
            AgentOpsLocal Dashboard
          </h1>
          <p className="text-slate-400 mt-2">Real-time LLM Telemetry & Cost Analyzer</p>
        </div>
        <div className="flex gap-4">
          <select 
            value={selectedEnv} 
            onChange={(e) => setSelectedEnv(e.target.value)}
            className="bg-slate-800 text-white border border-slate-700 px-4 py-2 rounded-lg font-medium shadow-lg outline-none"
          >
            <option value="">All Environments</option>
            <option value="dev">Development</option>
            <option value="staging">Staging</option>
            <option value="prod">Production</option>
          </select>
          <button 
            onClick={() => window.open(`${API_BASE}/api/v1/analytics/export${selectedEnv ? '?env=' + selectedEnv : ''}`, '_blank')}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-lg"
          >
            Export Data (JSON)
          </button>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center gap-4 text-emerald-400 mb-2">
            <DollarSign />
            <h3 className="font-semibold text-lg">Total Cost</h3>
          </div>
          <p className="text-4xl font-bold">${summary?.total_cost.toFixed(4) || "0.00"}</p>
          {summary?.daily_budget > 0 && (
            <div className="mt-4">
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Budget Progress</span>
                <span>${summary.total_cost.toFixed(2)} / ${summary.daily_budget.toFixed(2)}</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${summary.total_cost >= summary.daily_budget ? 'bg-red-500' : 'bg-emerald-500'}`}
                  style={{ width: `${Math.min((summary.total_cost / summary.daily_budget) * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center gap-4 text-blue-400 mb-2">
            <Layers />
            <h3 className="font-semibold text-lg">Total API Calls</h3>
          </div>
          <p className="text-4xl font-bold">{summary?.total_calls || 0}</p>
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center gap-4 text-purple-400 mb-2">
            <Activity />
            <h3 className="font-semibold text-lg">Total Tokens</h3>
          </div>
          <p className="text-4xl font-bold">{summary?.total_tokens || 0}</p>
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center gap-4 text-amber-400 mb-2">
            <Clock />
            <h3 className="font-semibold text-lg">Avg Latency</h3>
          </div>
          <p className="text-4xl font-bold">{summary?.avg_latency_ms.toFixed(0) || 0} ms</p>
        </div>
      </div>

      {/* Charts Section */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h2 className="text-xl font-bold text-white mb-4">Cost Over Time</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={Object.entries(summary.cost_over_time || {}).map(([date, cost]) => ({ date, cost }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={(value) => `$${value.toFixed(2)}`} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                    formatter={(value) => [`$${Number(value).toFixed(4)}`, 'Cost']}
                  />
                  <Line type="monotone" dataKey="cost" stroke="#34d399" strokeWidth={3} dot={{ r: 4, fill: '#34d399' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h2 className="text-xl font-bold text-white mb-4">Cost by Model</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={Object.entries(summary.by_model || {}).map(([name, value]) => ({ name, value }))}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {Object.entries(summary.by_model || {}).map((entry, index) => {
                      const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b'];
                      return <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />;
                    })}
                  </Pie>
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                    formatter={(value) => [`$${Number(value).toFixed(4)}`, 'Cost']}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap justify-center gap-4 mt-2">
                {Object.entries(summary.by_model || {}).map(([name, value], index) => {
                  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b'];
                  return (
                    <div key={name} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                      <span className="text-sm text-slate-300">{name} (${value.toFixed(2)})</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Anomalies Section */}
      {anomalies.length > 0 && (
        <div className="bg-red-900/20 border border-red-700/50 rounded-xl p-6 mb-8 shadow-lg">
          <div className="flex items-center gap-2 text-red-400 mb-4">
            <Activity />
            <h2 className="text-xl font-bold">Cost Anomalies Detected ({anomalies.length})</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {anomalies.map((anomaly) => (
              <div key={anomaly.call_id} className="bg-red-950/50 p-4 rounded-lg border border-red-800/50">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-semibold text-red-300">{anomaly.task_name}</span>
                  <span className="px-2 py-1 text-xs font-bold rounded-full bg-red-800 text-red-200">
                    {anomaly.severity}
                  </span>
                </div>
                <p className="text-sm text-red-200">
                  Cost: <span className="font-bold text-red-400">${anomaly.cost.toFixed(4)}</span> 
                  <span className="text-red-400/70 ml-1">(Avg: ${anomaly.avg_cost.toFixed(4)})</span>
                </p>
                <p className="text-sm text-red-200">
                  Tokens: <span className="font-bold text-red-400">{anomaly.total_tokens}</span>
                  <span className="text-red-400/70 ml-1">(Avg: {anomaly.avg_tokens.toFixed(0)})</span>
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Calls Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white">Recent LLM Calls</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-900 text-slate-400 text-sm uppercase">
              <tr>
                <th className="p-4 font-medium w-10"></th>
                <th className="p-4 font-medium">Task Name</th>
                <th className="p-4 font-medium">Agent ID</th>
                <th className="p-4 font-medium">Model</th>
                <th className="p-4 font-medium">Tokens</th>
                <th className="p-4 font-medium">Latency</th>
                <th className="p-4 font-medium">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {calls.map((call) => (
                <React.Fragment key={call.id}>
                  <tr 
                    onClick={() => toggleRow(call.id)}
                    className="hover:bg-slate-700/50 transition-colors cursor-pointer"
                  >
                    <td className="p-4 text-slate-400">
                      {expandedRows.has(call.id) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </td>
                    <td className="p-4 font-medium text-blue-300">{call.task_name}</td>
                    <td className="p-4 text-slate-400">
                      <div className="flex flex-col gap-1">
                        <span>{call.agent_id || '-'}</span>
                        {call.session_id && (
                          <button 
                            onClick={(e) => { e.stopPropagation(); viewSessionTrace(call.session_id); }}
                            className="text-xs bg-slate-700/50 hover:bg-slate-700 text-blue-300 px-2 py-1 rounded flex items-center w-fit gap-1"
                          >
                            <ListTree size={12} /> Trace
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="px-2 py-1 bg-slate-700 rounded-md text-xs">{call.model}</span>
                    </td>
                    <td className="p-4 text-slate-300">{call.total_tokens}</td>
                    <td className="p-4 text-slate-300">{call.latency_ms.toFixed(0)} ms</td>
                    <td className="p-4 text-emerald-400 font-medium">${call.cost.toFixed(5)}</td>
                  </tr>
                  {expandedRows.has(call.id) && (
                    <tr className="bg-slate-900/50">
                      <td colSpan="7" className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <h4 className="text-slate-400 text-xs uppercase mb-2 font-bold">Prompt</h4>
                            <pre className="bg-slate-950 p-3 rounded text-sm text-slate-300 overflow-x-auto max-h-60 whitespace-pre-wrap">
                              {typeof call.prompt === 'string' ? call.prompt : JSON.stringify(call.prompt, null, 2)}
                            </pre>
                          </div>
                          <div>
                            <h4 className="text-slate-400 text-xs uppercase mb-2 font-bold">Response</h4>
                            <pre className="bg-slate-950 p-3 rounded text-sm text-emerald-300 overflow-x-auto max-h-60 whitespace-pre-wrap">
                              {typeof call.response === 'string' ? call.response : JSON.stringify(call.response, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
              {calls.length === 0 && (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-500">
                    No API calls logged yet. Route your traffic through /api/v1/ingest
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      {/* Session Modal */}
      {activeSession && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-900 rounded-t-xl">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <ListTree className="text-blue-400" />
                Session Trace: <span className="text-blue-300 font-mono text-sm">{activeSession}</span>
              </h2>
              <button onClick={() => setActiveSession(null)} className="text-slate-400 hover:text-white transition-colors">
                <X />
              </button>
            </div>
            <div className="p-6 overflow-y-auto space-y-6">
              {sessionCalls.map((call, index) => (
                <div key={call.id} className="relative pl-8 border-l-2 border-slate-700 pb-2">
                  <div className="absolute -left-2 top-0 w-4 h-4 rounded-full bg-blue-500 border-4 border-slate-800"></div>
                  <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50">
                    <div className="flex justify-between mb-2">
                      <h3 className="font-bold text-blue-300">Step {index + 1}: {call.task_name}</h3>
                      <div className="flex gap-2 text-xs">
                        <span className="px-2 py-1 bg-slate-800 rounded">{call.model}</span>
                        <span className="px-2 py-1 bg-emerald-900/50 text-emerald-300 rounded">${call.cost.toFixed(5)}</span>
                        <span className="px-2 py-1 bg-slate-800 rounded text-slate-300">{call.latency_ms.toFixed(0)}ms</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div>
                        <h4 className="text-slate-400 text-xs uppercase mb-1 font-bold">Prompt</h4>
                        <pre className="bg-slate-950 p-2 rounded text-xs text-slate-300 overflow-x-auto max-h-40 whitespace-pre-wrap">
                          {typeof call.prompt === 'string' ? call.prompt : JSON.stringify(call.prompt, null, 2)}
                        </pre>
                      </div>
                      <div>
                        <h4 className="text-slate-400 text-xs uppercase mb-1 font-bold">Response</h4>
                        <pre className="bg-slate-950 p-2 rounded text-xs text-emerald-300 overflow-x-auto max-h-40 whitespace-pre-wrap">
                          {typeof call.response === 'string' ? call.response : JSON.stringify(call.response, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
