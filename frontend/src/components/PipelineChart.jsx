import React from 'react';

export const PipelineChart = ({ pipeline = [] }) => {
  const maxCount = Math.max(...pipeline.map((p) => p.count || 0), 1);
  const total = pipeline.reduce((acc, curr) => acc + (curr.count || 0), 0);

  return (
    <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800/80">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-base font-bold text-white">Outreach Pipeline Distribution</h3>
          <p className="text-xs text-slate-400 mt-0.5">Live CRM state breakdown across all influencer leads</p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          Total Leads: <strong className="text-white">{total}</strong>
        </span>
      </div>

      <div className="space-y-3.5">
        {pipeline.map((stage) => {
          const count = stage.count || 0;
          const barWidth = Math.max(4, Math.round((count / maxCount) * 100));
          const pctOfTotal = total > 0 ? Math.round((count / total) * 100) : 0;

          return (
            <div key={stage.stage} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-300 flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full inline-block"
                    style={{ backgroundColor: stage.color || '#8b5cf6' }}
                  />
                  {stage.stage}
                </span>
                <span className="text-slate-400 font-mono">
                  <span className="text-white font-bold">{count}</span> ({pctOfTotal}%)
                </span>
              </div>

              <div className="h-2.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800/50 p-0.5">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${count > 0 ? barWidth : 0}%`,
                    backgroundColor: stage.color || '#8b5cf6',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PipelineChart;
