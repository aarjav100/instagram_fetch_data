import React from 'react';
import {
  Users,
  Send,
  MessageSquare,
  ThumbsUp,
  CheckCheck,
  Zap,
  ArrowUpRight,
  Sparkles,
  Target,
  MailCheck,
} from 'lucide-react';
import StatCard from '../components/StatCard';
import PipelineChart from '../components/PipelineChart';

export const Dashboard = ({ stats, setActiveTab, onRefresh }) => {
  if (!stats) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
      </div>
    );
  }

  const {
    total_leads = 0,
    emails_sent = 0,
    replies = 0,
    interested = 0,
    collaborations_confirmed = 0,
    daily_sent_count = 0,
    daily_limit = 30,
    pipeline = [],
  } = stats;

  const replyRate = emails_sent > 0 ? Math.round((replies / emails_sent) * 100) : 0;
  const conversionRate = emails_sent > 0 ? Math.round((collaborations_confirmed / emails_sent) * 100) : 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Hero Welcome & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-purple-950/60 via-slate-900 to-indigo-950/40 border border-purple-500/20 shadow-xl">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            AI Autonomous Outreach Active
          </div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
            Influencer Automation Overview
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-xl">
            Targeting creators, evaluating audience relevance with Claude, and managing Gmail outreach threads with strict human oversight.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setActiveTab('campaign')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-all shadow-lg shadow-purple-600/30"
          >
            <Target className="w-4 h-4" />
            New Research
          </button>
          <button
            onClick={() => setActiveTab('emails')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold text-xs transition-all"
          >
            <MailCheck className="w-4 h-4 text-purple-400" />
            Approval Queue
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Leads"
          value={total_leads}
          icon={Users}
          color="purple"
          subtitle="Discovered & imported"
        />
        <StatCard
          title="Emails Sent"
          value={emails_sent}
          icon={Send}
          color="blue"
          subtitle={`${daily_sent_count} sent today`}
        />
        <StatCard
          title="Inbound Replies"
          value={replies}
          icon={MessageSquare}
          color="amber"
          subtitle={`${replyRate}% reply rate`}
        />
        <StatCard
          title="Interested Leads"
          value={interested}
          icon={ThumbsUp}
          color="emerald"
          subtitle="Positive sentiment"
        />
        <StatCard
          title="Collabs Confirmed"
          value={collaborations_confirmed}
          icon={CheckCheck}
          color="emerald"
          subtitle={`${conversionRate}% campaign conversion`}
        />
      </div>

      {/* Pipeline Status Chart & Action Highlights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PipelineChart pipeline={pipeline} />
        </div>

        {/* Outreach Capacity & Guardrails */}
        <div className="space-y-4">
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800/80 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Daily Gmail Safe Quota
                </span>
                <Zap className="w-4 h-4 text-amber-400" />
              </div>

              <div className="text-3xl font-extrabold text-white">
                {daily_sent_count} <span className="text-slate-500 text-lg">/ {daily_limit}</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {Math.max(0, daily_limit - daily_sent_count)} sends remaining today before anti-spam throttle kicks in.
              </p>

              <div className="w-full bg-slate-950 rounded-full h-2.5 mt-4 overflow-hidden border border-slate-800">
                <div
                  className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.round((daily_sent_count / daily_limit) * 100))}%` }}
                />
              </div>
            </div>

            <div className="mt-6 pt-5 border-t border-slate-800 text-xs text-slate-400 space-y-2">
              <div className="flex items-center justify-between">
                <span>Send Delay Between Messages</span>
                <span className="font-mono text-slate-200">2-5 seconds</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Human Approval Requirement</span>
                <span className="text-emerald-400 font-semibold">Strictly Enforced</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Auto-Stop on Opt-Out</span>
                <span className="text-emerald-400 font-semibold">Active</span>
              </div>
            </div>
          </div>

          {/* Quick jump to CRM */}
          <div
            onClick={() => setActiveTab('influencers')}
            className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950/40 to-slate-900 border border-indigo-500/20 hover:border-indigo-500/40 cursor-pointer transition-all flex items-center justify-between group"
          >
            <div>
              <div className="text-sm font-bold text-white group-hover:text-purple-300 transition-colors">
                View Influencer CRM Table
              </div>
              <div className="text-xs text-slate-400 mt-0.5">Filter by AI relevance score and manage custom notes</div>
            </div>
            <ArrowUpRight className="w-5 h-5 text-indigo-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
