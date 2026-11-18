import React, { useState, useEffect } from 'react';
import {
  MailCheck,
  Send,
  CheckCircle,
  XCircle,
  Edit3,
  Clock,
  AlertTriangle,
  Zap,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import api from '../api';
import { useToast } from '../context/ToastContext';

export const EmailApprovalQueue = ({ onRefresh }) => {
  const toast = useToast();
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState({ sent_today: 0, daily_limit: 30, remaining: 30 });
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [statusFilter, setStatusFilter] = useState('Pending Approval');

  // Editing state
  const [editingId, setEditingId] = useState(null);
  const [editSubject, setEditSubject] = useState('');
  const [editBody, setEditBody] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [qRes, sRes] = await Promise.all([
        api.getEmailQueue(statusFilter || undefined),
        api.getEmailStats(),
      ]);
      setEmails(qRes.data);
      setStats(sRes.data);
    } catch {
      toast.error('Failed to load email queue.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const handleApprove = async (id, updatedSubject, updatedBody) => {
    try {
      await api.approveEmail(id, {
        subject: updatedSubject,
        body: updatedBody,
      });
      toast.success('Email approved! Ready for sending.');
      setEditingId(null);
      loadData();
      if (onRefresh) onRefresh();
    } catch {
      toast.error('Failed to approve email.');
    }
  };

  const handleReject = async (id) => {
    try {
      await api.rejectEmail(id);
      toast.info('Email rejected.');
      loadData();
      if (onRefresh) onRefresh();
    } catch {
      toast.error('Failed to reject email.');
    }
  };

  const handleSendAllApproved = async () => {
    const approvedList = emails.filter((e) => e.status === 'Approved');
    if (approvedList.length === 0) {
      toast.info('No approved emails ready to send. Approve some drafts first.');
      return;
    }

    setSending(true);
    try {
      const res = await api.sendApprovedEmails();
      toast.success(res.data.message || `Dispatched ${res.data.sent_count} emails via Gmail API!`);
      loadData();
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error during send execution.');
    } finally {
      setSending(false);
    }
  };

  const startEdit = (email) => {
    setEditingId(email.id);
    setEditSubject(email.subject);
    setEditBody(email.body);
  };

  const approvedCount = emails.filter((e) => e.status === 'Approved').length;

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-300">
      {/* Top Header & Daily Capacity Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>Email Approval Queue</span>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
              {emails.length} In Queue
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Human-in-the-loop review: inspect Claude-generated cold drafts, personalize them, and authorize Gmail dispatch.
          </p>
        </div>

        {/* Send Approved Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSendAllApproved}
            disabled={sending || approvedCount === 0}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs transition-all shadow-lg shadow-emerald-600/25 disabled:opacity-50"
          >
            {sending ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Sending with Throttling...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Send Approved ({approvedCount})</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Safety Quota Card */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold text-white flex items-center gap-2">
              <span>Gmail API Sending Guardrails</span>
              <span className="text-[10px] px-2 py-0.2 rounded-full bg-emerald-500/20 text-emerald-300 font-medium">
                Active Throttle
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Enforcing max {stats.daily_limit} sends per day with safe pauses between messages to protect domain reputation.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div>
            <span className="text-slate-400">Sent Today: </span>
            <span className="font-bold text-purple-400">{stats.sent_today}</span> / {stats.daily_limit}
          </div>
          <div className="w-24 h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-purple-500 h-full rounded-full transition-all"
              style={{ width: `${Math.min(100, Math.round((stats.sent_today / stats.daily_limit) * 100))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3 text-xs font-semibold">
        {['Pending Approval', 'Approved', 'Sent', 'Rejected', ''].map((st) => (
          <button
            key={st || 'All'}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              statusFilter === st
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            {st || 'All Emails'}
          </button>
        ))}
      </div>

      {/* Emails List */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <span>Loading outreach emails...</span>
          </div>
        ) : emails.length === 0 ? (
          <div className="p-12 text-center bg-slate-900/40 rounded-3xl border border-slate-800 text-slate-400 text-xs">
            No emails found in this queue state.
          </div>
        ) : (
          emails.map((email) => {
            const isEditMode = editingId === email.id;
            const inf = email.influencer || {};

            return (
              <div
                key={email.id}
                className={`p-6 rounded-3xl border transition-all duration-300 ${
                  email.status === 'Approved'
                    ? 'bg-emerald-950/20 border-emerald-500/30'
                    : email.status === 'Sent'
                    ? 'bg-slate-900/50 border-slate-800 opacity-80'
                    : 'bg-slate-900/90 border-slate-800 hover:border-purple-500/30'
                }`}
              >
                {/* Header row: Creator & Status */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
                  <div className="flex items-center gap-3">
                    <img
                      src={
                        inf.profile_pic_url ||
                        `https://api.dicebear.com/7.x/avataaars/svg?seed=${inf.username || 'creator'}`
                      }
                      alt={inf.name}
                      className="w-10 h-10 rounded-full bg-slate-800 object-cover border border-slate-700"
                    />
                    <div>
                      <div className="font-bold text-white text-sm flex items-center gap-2">
                        <span>{inf.name || 'Creator'}</span>
                        <span className="text-xs text-purple-400 font-mono">@{inf.username}</span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono">{email.recipient_email}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold border ${
                        email.status === 'Approved'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                          : email.status === 'Sent'
                          ? 'bg-sky-500/20 text-sky-300 border-sky-500/30'
                          : email.status === 'Rejected'
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                          : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                      }`}
                    >
                      {email.status}
                    </span>

                    {email.email_type && (
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 text-[10px] text-slate-400 font-mono uppercase">
                        {email.email_type}
                      </span>
                    )}
                  </div>
                </div>

                {/* Email Body & Subject */}
                <div className="mt-4 space-y-3">
                  {isEditMode ? (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs font-semibold text-slate-400 mb-1">Subject Line</label>
                        <input
                          type="text"
                          value={editSubject}
                          onChange={(e) => setEditSubject(e.target.value)}
                          className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-semibold focus:outline-none focus:border-purple-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-400 mb-1">Email Body</label>
                        <textarea
                          rows={6}
                          value={editBody}
                          onChange={(e) => setEditBody(e.target.value)}
                          className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-purple-500"
                        />
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                        <span className="text-slate-400 text-xs font-normal">Subject:</span>
                        <span>{email.subject}</span>
                      </div>
                      <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-300 font-mono whitespace-pre-line leading-relaxed">
                        {email.body}
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Controls */}
                <div className="mt-5 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="text-slate-500 text-[11px]">
                    Created: {new Date(email.created_at).toLocaleString()}
                    {email.sent_at && ` • Dispatched: ${new Date(email.sent_at).toLocaleTimeString()}`}
                  </div>

                  <div className="flex items-center gap-2">
                    {isEditMode ? (
                      <>
                        <button
                          onClick={() => setEditingId(null)}
                          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleApprove(email.id, editSubject, editBody)}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
                        >
                          Save & Approve
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => startEdit(email)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-medium"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>

                        {email.status !== 'Approved' && (
                          <button
                            onClick={() => handleApprove(email.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600 text-emerald-300 hover:text-white font-medium transition-colors"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Approve</span>
                          </button>
                        )}

                        {email.status !== 'Rejected' && email.status !== 'Sent' && (
                          <button
                            onClick={() => handleReject(email.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white font-medium transition-colors"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Reject</span>
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default EmailApprovalQueue;
