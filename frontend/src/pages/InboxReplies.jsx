import React, { useState, useEffect } from 'react';
import {
  Inbox,
  Sparkles,
  Send,
  MessageSquare,
  CheckCircle2,
  Clock,
  RefreshCw,
  Edit3,
  Tag,
  ThumbsUp,
  XCircle,
  HelpCircle,
  DollarSign,
  PlusCircle,
} from 'lucide-react';
import api from '../api';
import { useToast } from '../context/ToastContext';

export const InboxReplies = ({ onRefresh }) => {
  const toast = useToast();
  const [replies, setReplies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);

  // Draft editing state
  const [editingId, setEditingId] = useState(null);
  const [draftText, setDraftText] = useState('');
  const [sendingId, setSendingId] = useState(null);

  // Simulation test state
  const [showSimulate, setShowSimulate] = useState(false);
  const [simInfluencerId, setSimInfluencerId] = useState('');
  const [simText, setSimText] = useState('Hey Alex, this sounds super interesting! Send over the details and rates.');
  const [simulating, setSimulating] = useState(false);
  const [influencerList, setInfluencerList] = useState([]);

  const loadReplies = async () => {
    setLoading(true);
    try {
      const [rRes, infRes] = await Promise.all([
        api.getReplies(),
        api.getInfluencers(),
      ]);
      setReplies(rRes.data);
      setInfluencerList(infRes.data);
      if (infRes.data.length > 0 && !simInfluencerId) {
        setSimInfluencerId(infRes.data[0].id);
      }
    } catch {
      toast.error('Failed to load inbound replies.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReplies();
  }, []);

  const handlePollNow = async () => {
    setPolling(true);
    try {
      const res = await api.pollReplies();
      toast.success(res.data.message || 'Gmail thread polling completed.');
      loadReplies();
      if (onRefresh) onRefresh();
    } catch {
      toast.error('Failed to poll Gmail threads.');
    } finally {
      setPolling(false);
    }
  };

  const handleSendDraft = async (replyId) => {
    setSendingId(replyId);
    try {
      // First update draft if edited
      if (editingId === replyId) {
        await api.approveReply(replyId, { draft_reply: draftText });
      }

      await api.sendReply(replyId);
      toast.success('Approved draft reply sent successfully in Gmail thread!');
      setEditingId(null);
      loadReplies();
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to dispatch reply.');
    } finally {
      setSendingId(null);
    }
  };

  const handleSimulateReply = async (e) => {
    e.preventDefault();
    if (!simInfluencerId || !simText.trim()) {
      toast.error('Please select an influencer and enter reply text.');
      return;
    }

    setSimulating(true);
    try {
      const res = await api.simulateReply({
        influencer_id: Number(simInfluencerId),
        reply_text: simText,
      });
      toast.success(
        `Claude classified as '${res.data.category}' and generated draft reply!`
      );
      setShowSimulate(false);
      loadReplies();
      if (onRefresh) onRefresh();
    } catch {
      toast.error('Failed to simulate reply.');
    } finally {
      setSimulating(false);
    }
  };

  const getCategoryBadge = (category) => {
    const map = {
      interested: {
        bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
        icon: ThumbsUp,
        label: 'Interested',
      },
      not_interested: {
        bg: 'bg-slate-700/50 text-slate-400 border-slate-700',
        icon: XCircle,
        label: 'Not Interested',
      },
      pricing_enquiry: {
        bg: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
        icon: DollarSign,
        label: 'Pricing Enquiry',
      },
      collaboration_request: {
        bg: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
        icon: Sparkles,
        label: 'Collab Request',
      },
      opt_out: {
        bg: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
        icon: XCircle,
        label: 'Opt Out',
      },
      other: {
        bg: 'bg-slate-800 text-slate-300 border-slate-700',
        icon: HelpCircle,
        label: 'General / Other',
      },
    };

    const cfg = map[category] || map.other;
    const Icon = cfg.icon;

    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${cfg.bg}`}
      >
        <Icon className="w-3.5 h-3.5" />
        <span>{cfg.label}</span>
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-300">
      {/* Top Header & Quick Buttons */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>Inbox & AI Reply Management</span>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
              {replies.length} Messages
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            APScheduler polls threads periodically. Claude classifies intent, recommends next actions, and generates response drafts requiring human approval.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSimulate(!showSimulate)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
          >
            <PlusCircle className="w-3.5 h-3.5 text-purple-400" />
            <span>Simulate Reply</span>
          </button>

          <button
            onClick={handlePollNow}
            disabled={polling}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-all shadow-md shadow-purple-600/30 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${polling ? 'animate-spin' : ''}`} />
            <span>Poll Gmail Threads</span>
          </button>
        </div>
      </div>

      {/* Simulator Dropdown Form */}
      {showSimulate && (
        <form
          onSubmit={handleSimulateReply}
          className="p-6 rounded-3xl bg-slate-900 border border-purple-500/40 shadow-2xl space-y-4 animate-in slide-in-from-top-4"
        >
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2 text-sm font-bold text-white">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>Simulate Inbound Creator Email</span>
            </div>
            <button
              type="button"
              onClick={() => setShowSimulate(false)}
              className="text-xs text-slate-400 hover:text-white"
            >
              ✕ Close
            </button>
          </div>

          <p className="text-xs text-slate-400">
            Test how Claude triages different replies (e.g. asking for rates, confirming interest, or requesting unsubscribe).
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Select Influencer Lead
              </label>
              <select
                value={simInfluencerId}
                onChange={(e) => setSimInfluencerId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-purple-500"
              >
                {influencerList.map((inf) => (
                  <option key={inf.id} value={inf.id}>
                    {inf.name} (@{inf.username})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Quick Template Samples
              </label>
              <div className="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={() => setSimText("Hey! I'd love to collaborate on the summer launch. Can you send the brief?")}
                  className="px-2 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300"
                >
                  Interested
                </button>
                <button
                  type="button"
                  onClick={() => setSimText("Hi Alex, my standard sponsored reel rate is $400. Let me know if that works.")}
                  className="px-2 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300"
                >
                  Pricing Enquiry
                </button>
                <button
                  type="button"
                  onClick={() => setSimText("Thanks, but I am not taking sponsorships right now. Please unsubscribe.")}
                  className="px-2 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300"
                >
                  Opt Out
                </button>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Inbound Email Message Text
            </label>
            <textarea
              rows={3}
              value={simText}
              onChange={(e) => setSimText(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="submit"
              disabled={simulating}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs transition-all shadow-md shadow-purple-600/30 flex items-center gap-2"
            >
              {simulating && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />}
              <span>Process with Claude</span>
            </button>
          </div>
        </form>
      )}

      {/* Replies Feed */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <span>Loading inbound messages...</span>
          </div>
        ) : replies.length === 0 ? (
          <div className="p-12 text-center bg-slate-900/40 rounded-3xl border border-slate-800 text-slate-400 text-xs space-y-2">
            <Inbox className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-white font-bold text-sm">No inbound replies recorded yet</div>
            <p className="text-[11px] max-w-sm mx-auto">
              Incoming Gmail thread messages will show up here automatically classified by Claude with suggested next steps.
            </p>
          </div>
        ) : (
          replies.map((reply) => {
            const isEditingThis = editingId === reply.id;
            const inf = reply.influencer || {};

            return (
              <div
                key={reply.id}
                className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800/80 hover:border-purple-500/30 transition-all shadow-xl space-y-4"
              >
                {/* Header: Sender & Sentiment Tag */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
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
                        <span>{inf.name || 'Influencer'}</span>
                        <span className="text-xs text-purple-400 font-mono">@{inf.username}</span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono">{reply.sender_email}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {getCategoryBadge(reply.category)}
                    <span className="text-[11px] text-slate-500 font-mono">
                      {new Date(reply.received_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Inbound Message Snippet/Body */}
                <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-line leading-relaxed">
                  {reply.body || reply.snippet}
                </div>

                {/* Claude Recommendation Box */}
                {reply.suggested_next_action && (
                  <div className="p-3.5 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 text-xs flex items-start gap-2.5">
                    <Sparkles className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-purple-300">AI Suggested Next Action: </span>
                      <span className="text-slate-300">{reply.suggested_next_action}</span>
                    </div>
                  </div>
                )}

                {/* Claude Draft Reply Box (Editable & Sendable) */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-purple-950/20 to-slate-950 border border-purple-500/20 space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="text-purple-300 flex items-center gap-1.5">
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>AI Generated Draft Reply (Requires Approval)</span>
                    </span>

                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        reply.draft_status === 'Sent'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-amber-500/20 text-amber-300'
                      }`}
                    >
                      {reply.draft_status}
                    </span>
                  </div>

                  {isEditingThis ? (
                    <textarea
                      rows={4}
                      value={draftText}
                      onChange={(e) => setDraftText(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-purple-500/40 text-xs text-slate-100 font-mono leading-relaxed focus:outline-none"
                    />
                  ) : (
                    <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 font-mono whitespace-pre-line leading-relaxed">
                      {reply.draft_reply || 'No draft reply generated.'}
                    </div>
                  )}

                  {/* Actions Bar */}
                  <div className="pt-2 flex items-center justify-end gap-2 text-xs">
                    {reply.draft_status !== 'Sent' && (
                      <>
                        {isEditingThis ? (
                          <button
                            onClick={() => setEditingId(null)}
                            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                          >
                            Cancel
                          </button>
                        ) : (
                          <button
                            onClick={() => {
                              setEditingId(reply.id);
                              setDraftText(reply.draft_reply || '');
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                          >
                            <Edit3 className="w-3 h-3" />
                            <span>Edit Draft</span>
                          </button>
                        )}

                        <button
                          onClick={() => handleSendDraft(reply.id)}
                          disabled={sendingId === reply.id}
                          className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold transition-all shadow-md shadow-emerald-600/25 disabled:opacity-50"
                        >
                          {sendingId === reply.id ? (
                            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Send className="w-3.5 h-3.5" />
                          )}
                          <span>Approve & Send In Thread</span>
                        </button>
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

export default InboxReplies;
