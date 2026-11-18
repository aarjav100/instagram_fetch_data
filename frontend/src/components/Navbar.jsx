import React, { useEffect, useState } from 'react';
import { Sparkles, Activity, Mail, RefreshCw, Send, ShieldCheck } from 'lucide-react';
import api from '../api';

export const Navbar = ({ onRefresh, isRefreshing }) => {
  const [stats, setStats] = useState({ sent_today: 0, daily_limit: 30, remaining: 30 });
  const [health, setHealth] = useState({ status: 'connecting' });

  const loadNavData = async () => {
    try {
      const [hRes, sRes] = await Promise.all([
        api.getHealth().catch(() => ({ data: { status: 'offline' } })),
        api.getEmailStats().catch(() => ({ data: { sent_today: 0, daily_limit: 30 } })),
      ]);
      setHealth(hRes.data);
      setStats(sRes.data);
    } catch {
      setHealth({ status: 'offline' });
    }
  };

  useEffect(() => {
    loadNavData();
    const timer = setInterval(loadNavData, 15000);
    return () => clearInterval(timer);
  }, []);

  const percentage = Math.min(100, Math.round((stats.sent_today / (stats.daily_limit || 30)) * 100));

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Brand & Title */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-base bg-gradient-to-r from-white via-slate-200 to-purple-300 bg-clip-text text-transparent">
              AuraReach
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
              AI Outreach v1.0
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            Instagram Discovery • Claude Filter • Gmail Automation
          </p>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Daily Send Limit Indicator */}
        <div className="hidden md:flex items-center gap-3 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
          <div className="flex items-center gap-1.5 text-slate-300 font-medium">
            <Send className="w-3.5 h-3.5 text-purple-400" />
            <span>Daily Send Limit:</span>
            <span className="font-mono text-purple-300 font-bold">
              {stats.sent_today} / {stats.daily_limit}
            </span>
          </div>
          <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700/50">
            <div
              className={`h-full transition-all duration-500 ${
                percentage > 85 ? 'bg-rose-500' : percentage > 50 ? 'bg-amber-400' : 'bg-purple-500'
              }`}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>

        {/* Backend Status Badge */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            health.status === 'healthy'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}
          title={health.status === 'healthy' ? 'FastAPI Backend Online' : 'Backend Disconnected'}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              health.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
            }`}
          />
          <span className="capitalize">{health.status === 'healthy' ? 'Online' : 'Offline'}</span>
        </div>

        {/* Refresh Button */}
        <button
          onClick={() => {
            onRefresh && onRefresh();
            loadNavData();
          }}
          disabled={isRefreshing}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all disabled:opacity-50"
          title="Refresh All Data"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-purple-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};

export default Navbar;
