import React, { useState, useEffect } from 'react';
import {
  Clock,
  Sparkles,
  Send,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Mail,
  ExternalLink,
  ShieldCheck,
} from 'lucide-react';
import api from '../api';
import { useToast } from '../context/ToastContext';

export const FollowUps = ({ setActiveTab, onRefresh }) => {
  const toast = useToast();
  const [dueFollowups, setDueFollowups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [generatingId, setGeneratingId] = useState(null);

  const loadDue = async () => {
    setLoading(true);
    try {
      const res = await api.getDueFollowups();
      setDueFollowups(res.data);
    } catch {
      toast.error('Failed to load due follow-ups.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDue();
  }, []);

  const handleManualCheck = async () => {
    setTriggering(true);
    try {
      const res = await api.triggerFollowupCheck();
      toast.success(res.data.message || 'Follow-up evaluation complete.');
      loadDue();
      if (onRefresh) onRefresh();
    } catch {
      toast.error('Error running follow-up check.');
    } finally {
      setTriggering(false);
    }
  };

  const handleGenerateDraft = async (influencerId) => {
    setGeneratingId(influencerId);
    try {
      await api.generateFollowup(influencerId);
      toast.success('Generated follow-up draft! Ready in Email Approval Queue.');
      loadDue();
      if (onRefresh) onRefresh();
      if (setActiveTab) setActiveTab('emails');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate follow-up.');
    } finally {
      setGeneratingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-300">
      {/* Header & Trigger */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>Automated Follow-up Sequences</span>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {dueFollowups.length} Leads Due
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            APScheduler evaluates sent threads every hour: Follow-up 1 (after 3-5 days) and Follow-up 2 (after 5-7 more days). Same Gmail thread.
          </p>
        </div>

        <button
          onClick={handleManualCheck}
          disabled={triggering}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-all shadow-md shadow-purple-600/30 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${triggering ? 'animate-spin' : ''}`} />
          <span>Run Follow-up Check Now</span>
        </button>
      </div>

      {/* Rules Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-xs space-y-1">
          <div className="font-bold text-white flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-400" />
            <span>Step 1: First Follow-up</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Triggered 3-5 days after initial cold email if no inbound reply is detected.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-xs space-y-1">
          <div className="font-bold text-white flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>Step 2: Polite Break-up</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Triggered 5-7 days after Follow-up 1. Caps at maximum 2 follow-ups per creator.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-xs space-y-1">
          <div className="font-bold text-emerald-400 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" />
            <span>Auto-Stop Protection</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Sequences automatically halt instantly if lead status becomes Replied, Not Interested, or Opted Out.
          </p>
        </div>
      </div>

      {/* List of Leads Due for Follow-up */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <span>Checking lead timelines...</span>
          </div>
        ) : dueFollowups.length === 0 ? (
          <div className="p-12 text-center bg-slate-900/40 rounded-3xl border border-slate-800 text-slate-400 text-xs space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
            <div className="text-white font-bold text-sm">No follow-ups due right now!</div>
            <p className="text-[11px] max-w-md mx-auto">
              All active email threads are either replied to, recent, or have completed their sequences.
            </p>
          </div>
        ) : (
          dueFollowups.map((item) => (
            <div
              key={item.influencer_id}
              className="p-6 rounded-3xl bg-slate-900/90 border border-amber-500/30 hover:border-amber-500/50 shadow-xl transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold text-sm">
                    {item.next_step}
                  </div>

                  <div>
                    <div className="font-bold text-white text-base flex items-center gap-2">
                      <span>{item.name}</span>
                      <span className="text-xs text-purple-400 font-mono">@{item.username}</span>
                    </div>
                    <div className="text-xs text-slate-400 font-mono mt-0.5">{item.email}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right text-xs">
                    <span className="text-slate-400">Last outreach: </span>
                    <span className="font-bold text-amber-300 font-mono">
                      {item.days_since_last_email} days ago
                    </span>
                    <div className="text-[11px] text-slate-500">Sent count: {item.followup_count} / 2</div>
                  </div>

                  <button
                    onClick={() => handleGenerateDraft(item.influencer_id)}
                    disabled={generatingId === item.influencer_id}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-bold text-xs shadow-md shadow-amber-600/30 transition-all disabled:opacity-50"
                  >
                    {generatingId === item.influencer_id ? (
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Sparkles className="w-3.5 h-3.5" />
                    )}
                    <span>Generate & Review Draft</span>
                  </button>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-300">Target Subject: </span>
                  <span className="font-mono text-slate-200">{item.suggested_subject}</span>
                </div>
                <div className="text-[11px] font-mono text-slate-500">
                  Thread ID: {item.thread_id || 'Initial Thread'}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default FollowUps;
