import React from 'react';

export const StatCard = ({ title, value, icon: Icon, color = 'purple', subtitle }) => {
  const colorMap = {
    purple: {
      border: 'border-purple-500/20 hover:border-purple-500/40',
      bg: 'bg-purple-500/10 text-purple-400',
      glow: 'from-purple-500/5',
    },
    emerald: {
      border: 'border-emerald-500/20 hover:border-emerald-500/40',
      bg: 'bg-emerald-500/10 text-emerald-400',
      glow: 'from-emerald-500/5',
    },
    blue: {
      border: 'border-blue-500/20 hover:border-blue-500/40',
      bg: 'bg-blue-500/10 text-blue-400',
      glow: 'from-blue-500/5',
    },
    amber: {
      border: 'border-amber-500/20 hover:border-amber-500/40',
      bg: 'bg-amber-500/10 text-amber-400',
      glow: 'from-amber-500/5',
    },
    rose: {
      border: 'border-rose-500/20 hover:border-rose-500/40',
      bg: 'bg-rose-500/10 text-rose-400',
      glow: 'from-rose-500/5',
    },
  };

  const scheme = colorMap[color] || colorMap.purple;

  return (
    <div
      className={`relative overflow-hidden p-5 rounded-2xl bg-slate-900/80 border ${scheme.border} transition-all duration-300 hover:shadow-xl hover:-translate-y-0.5 group`}
    >
      <div
        className={`absolute inset-0 bg-gradient-to-br ${scheme.glow} to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none`}
      />

      <div className="flex items-center justify-between mb-3 relative z-10">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        <div className={`p-2.5 rounded-xl ${scheme.bg} transition-transform group-hover:scale-110`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="relative z-10">
        <div className="text-3xl font-extrabold text-white tracking-tight">{value}</div>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
};

export default StatCard;
