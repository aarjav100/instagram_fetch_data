import React from 'react';
import {
  LayoutDashboard,
  Target,
  Users,
  MailCheck,
  Clock,
  Inbox,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab, pendingEmailCount = 0, dueFollowupCount = 0, replyCount = 0 }) => {
  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Analytics & Pipeline',
    },
    {
      id: 'campaign',
      label: 'Campaign Setup',
      icon: Target,
      description: 'Instagram Research',
    },
    {
      id: 'influencers',
      label: 'Influencer Table',
      icon: Users,
      description: 'AI Scoring & CRM',
    },
    {
      id: 'emails',
      label: 'Email Approval Queue',
      icon: MailCheck,
      badge: pendingEmailCount > 0 ? pendingEmailCount : null,
      description: 'Review & Send Outbox',
    },
    {
      id: 'followups',
      label: 'Follow-ups',
      icon: Clock,
      badge: dueFollowupCount > 0 ? dueFollowupCount : null,
      description: 'Sequence 1 & 2',
    },
    {
      id: 'inbox',
      label: 'Inbox / Replies',
      icon: Inbox,
      badge: replyCount > 0 ? replyCount : null,
      description: 'Claude Classified',
    },
  ];

  return (
    <aside className="w-64 shrink-0 bg-slate-950 border-r border-slate-800/80 flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
          Workflow Navigation
        </div>

        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full group flex items-center justify-between px-3 py-3 rounded-xl text-left transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-purple-900/40 to-indigo-900/30 text-white border border-purple-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`p-1.5 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-purple-600 text-white shadow-md shadow-purple-500/30'
                      : 'bg-slate-900 text-slate-400 group-hover:text-purple-400'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-semibold leading-tight">{item.label}</div>
                  <div className="text-[11px] text-slate-500 group-hover:text-slate-400 leading-tight mt-0.5">
                    {item.description}
                  </div>
                </div>
              </div>

              {item.badge ? (
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-purple-500 text-white shadow-sm">
                  {item.badge}
                </span>
              ) : (
                <ChevronRight
                  className={`w-4 h-4 text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity ${
                    isActive ? 'opacity-100 text-purple-400' : ''
                  }`}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* AI Assistant Info Box */}
      <div className="p-3.5 rounded-xl bg-gradient-to-br from-purple-950/40 via-indigo-950/20 to-slate-900 border border-purple-500/20 text-xs">
        <div className="flex items-center gap-2 text-purple-300 font-semibold mb-1">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>Claude 3.5 Active</span>
        </div>
        <p className="text-slate-400 text-[11px] leading-relaxed">
          Strictest JSON generation, relevance scoring, and automatic reply sentiment triage.
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;
