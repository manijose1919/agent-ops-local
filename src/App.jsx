import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, DollarSign, Clock, Layers } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [summary, setSummary] = useState(null);
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryRes, callsRes] = await Promise.all([
          axios.get(`${API_BASE}/api/v1/analytics/summary`),
          axios.get(`${API_BASE}/api/v1/calls`)
        ]);
        setSummary(summaryRes.data);
        setCalls(callsRes.data);
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
  }, []);

  if (loading && !summary) {
    return <div className="min-h-screen flex items-center justify-center">Loading Telemetry...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-900 p-8 text-slate-100 font-sans">
      <header className="mb-8 border-b border-slate-700 pb-4">
        <h1 className="text-3xl font-bold text-blue-400 flex items-center gap-2">
          <Activity className="w-8 h-8" />
          AgentOpsLocal Dashboard
        </h1>
        <p className="text-slate-400 mt-2">Real-time LLM Telemetry & Cost Analyzer</p>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center gap-4 text-emerald-400 mb-2">
            <DollarSign />
            <h3 className="font-semibold text-lg">Total Cost</h3>
          </div>
          <p className="text-4xl font-bold">${summary?.total_cost.toFixed(4) || "0.00"}</p>
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

      {/* Calls Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white">Recent LLM Calls</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-900 text-slate-400 text-sm uppercase">
              <tr>
                <th className="p-4 font-medium">Task Name</th>
                <th className="p-4 font-medium">Model</th>
                <th className="p-4 font-medium">Tokens</th>
                <th className="p-4 font-medium">Latency</th>
                <th className="p-4 font-medium">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {calls.map((call) => (
                <tr key={call.id} className="hover:bg-slate-700/50 transition-colors">
                  <td className="p-4 font-medium text-blue-300">{call.task_name}</td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-slate-700 rounded-md text-xs">{call.model}</span>
                  </td>
                  <td className="p-4 text-slate-300">{call.total_tokens}</td>
                  <td className="p-4 text-slate-300">{call.latency_ms.toFixed(0)} ms</td>
                  <td className="p-4 text-emerald-400 font-medium">${call.cost.toFixed(5)}</td>
                </tr>
              ))}
              {calls.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-slate-500">
                    No API calls logged yet. Route your traffic through /api/v1/ingest
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
