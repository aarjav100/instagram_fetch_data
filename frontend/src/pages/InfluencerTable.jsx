import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ExternalLink,
  Mail,
  Sparkles,
  ArrowUpDown,
  MoreVertical,
  Check,
  Trash2,
  Edit2,
  Send,
  UserCheck,
} from 'lucide-react';
import api from '../api';
import { useToast } from '../context/ToastContext';

export const InfluencerTable = ({ setActiveTab, onRefresh }) => {
  const toast = useToast();
  const [influencers, setInfluencers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [sortBy, setSortBy] = useState('score_desc');

  // Selected influencer for modal
  const [selectedInf, setSelectedInf] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ email: '', notes: '', status: '' });

  const loadInfluencers = async () => {
    setLoading(true);
    try {
      const params = {
        search: search || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        sort_by: sortBy,
      };
      const res = await api.getInfluencers(params);
      setInfluencers(res.data);
    } catch {
      toast.error('Failed to load influencers.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInfluencers();
  }, [search, statusFilter, priorityFilter, sortBy]);

  const handleStatusChange = async (id, newStatus) => {
    try {
      await api.updateInfluencer(id, { status: newStatus });
      setInfluencers((prev) =>
        prev.map((inf) => (inf.id === id ? { ...inf, status: newStatus } : inf))
      );
      toast.success(`Updated status to ${newStatus}`);
      if (onRefresh) onRefresh();
    } catch {
      toast.error('Failed to update status.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this creator from CRM?')) return;
    try {
      await api.deleteInfluencer(id);
      setInfluencers((prev) => prev.filter((inf) => inf.id !== id));
      toast.success('Influencer removed.');
      if (onRefresh) onRefresh();
    } catch {
      toast.error('Failed to delete influencer.');
    }
  };

  const handleGenerateSingle = async (influencer) => {
    if (!influencer.email) {
      toast.error('Cannot generate email: Creator has no email address.');
      return;
    }
    try {
      await api.generateEmails({
        influencer_ids: [influencer.id],
      });
      toast.success(`Cold email generated for ${influencer.name}! View in Approval Queue.`);
      if (setActiveTab) setActiveTab('emails');
    } catch {
      toast.error('Failed to generate email.');
    }
  };

  const openEditModal = (inf) => {
    setSelectedInf(inf);
    setEditForm({ email: inf.email || '', notes: inf.notes || '', status: inf.status });
    setIsEditing(true);
  };

  const saveEdit = async () => {
    if (!selectedInf) return;
    try {
      const res = await api.updateInfluencer(selectedInf.id, editForm);
      setInfluencers((prev) =>
        prev.map((inf) => (inf.id === selectedInf.id ? { ...inf, ...res.data } : inf))
      );
      toast.success('Creator details updated & synced to Google Sheets CRM!');
      setIsEditing(false);
    } catch {
      toast.error('Failed to update creator details.');
    }
  };

  const getStatusBadge = (status) => {
    const map = {
      'New Lead': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
      'Email Available': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      'Email Sent': 'bg-sky-500/10 text-sky-400 border-sky-500/20',
      'Follow-up Due': 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse',
      'Replied': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      'Interested': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 font-bold',
      'Collaboration Confirmed': 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30 font-bold',
      'Not Interested': 'bg-slate-700/50 text-slate-400 border-slate-700',
      'Opted Out': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    };
    return map[status] || 'bg-slate-800 text-slate-300 border-slate-700';
  };

  const getScoreBadge = (score) => {
    if (score >= 85) return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
    if (score >= 65) return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    return 'bg-rose-500/15 text-rose-300 border-rose-500/30';
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Page Heading & Search/Filters Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>Influencer CRM Directory</span>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
              {influencers.length} Creators
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Sort, filter, inspect AI evaluation notes, and manage communication status with Google Sheets syncing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('campaign')}
            className="px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-all shadow-md shadow-purple-600/25"
          >
            + Add Creators
          </button>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name, @username, email, or summary..."
            className="w-full pl-9 pr-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-purple-500"
          >
            <option value="">All Statuses</option>
            <option value="New Lead">New Lead</option>
            <option value="Email Available">Email Available</option>
            <option value="Email Sent">Email Sent</option>
            <option value="Follow-up Due">Follow-up Due</option>
            <option value="Replied">Replied</option>
            <option value="Interested">Interested</option>
            <option value="Collaboration Confirmed">Collaboration Confirmed</option>
            <option value="Not Interested">Not Interested</option>
            <option value="Opted Out">Opted Out</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-purple-500"
          >
            <option value="">All Priorities</option>
            <option value="High">High Priority</option>
            <option value="Medium">Medium Priority</option>
            <option value="Low">Low Priority</option>
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-purple-500"
          >
            <option value="score_desc">AI Score: High → Low</option>
            <option value="score_asc">AI Score: Low → High</option>
            <option value="followers_desc">Followers: High → Low</option>
            <option value="followers_asc">Followers: Low → High</option>
            <option value="recent">Recently Added</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Creator / Username</th>
                <th className="py-3.5 px-4">Niche</th>
                <th className="py-3.5 px-4">Followers</th>
                <th className="py-3.5 px-4">Business Email</th>
                <th className="py-3.5 px-4">AI Score</th>
                <th className="py-3.5 px-4">Claude Evaluation</th>
                <th className="py-3.5 px-4">CRM Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-slate-400">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                      <span>Loading creator records...</span>
                    </div>
                  </td>
                </tr>
              ) : influencers.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-slate-500">
                    No creators found matching current filters.
                  </td>
                </tr>
              ) : (
                influencers.map((inf) => (
                  <tr key={inf.id} className="hover:bg-slate-800/40 transition-colors group">
                    {/* Name & Avatar */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <img
                          src={
                            inf.profile_pic_url ||
                            `https://api.dicebear.com/7.x/avataaars/svg?seed=${inf.username}`
                          }
                          alt={inf.name}
                          className="w-8 h-8 rounded-full bg-slate-800 object-cover border border-slate-700"
                        />
                        <div>
                          <div className="font-bold text-white text-sm">{inf.name}</div>
                          <a
                            href={inf.profile_link || `https://instagram.com/${inf.username}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-purple-400 hover:text-purple-300 font-mono inline-flex items-center gap-1"
                          >
                            @{inf.username}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    </td>

                    {/* Niche */}
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-medium">
                        {inf.niche || inf.category || 'Creator'}
                      </span>
                    </td>

                    {/* Followers */}
                    <td className="py-3.5 px-4 font-mono text-slate-200">
                      {inf.followers.toLocaleString()}
                    </td>

                    {/* Email */}
                    <td className="py-3.5 px-4">
                      {inf.email ? (
                        <div className="flex items-center gap-1.5 text-slate-200 font-mono">
                          <Mail className="w-3.5 h-3.5 text-emerald-400" />
                          <span>{inf.email}</span>
                        </div>
                      ) : (
                        <span className="text-slate-500 italic">No email found</span>
                      )}
                    </td>

                    {/* AI Score */}
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-bold border ${getScoreBadge(
                          inf.relevance_score
                        )}`}
                      >
                        <Sparkles className="w-3 h-3" />
                        {inf.relevance_score}
                      </span>
                    </td>

                    {/* Claude Evaluation */}
                    <td className="py-3.5 px-4 max-w-xs">
                      <p
                        className="text-slate-300 line-clamp-2 leading-relaxed text-[11px]"
                        title={inf.suitability_reason || inf.profile_summary}
                      >
                        {inf.profile_summary || inf.suitability_reason || inf.bio}
                      </p>
                    </td>

                    {/* Status dropdown */}
                    <td className="py-3.5 px-4">
                      <select
                        value={inf.status}
                        onChange={(e) => handleStatusChange(inf.id, e.target.value)}
                        className={`px-2.5 py-1 rounded-full text-xs font-semibold border cursor-pointer focus:outline-none ${getStatusBadge(
                          inf.status
                        )}`}
                      >
                        <option value="New Lead">New Lead</option>
                        <option value="Email Available">Email Available</option>
                        <option value="Email Sent">Email Sent</option>
                        <option value="Follow-up Due">Follow-up Due</option>
                        <option value="Replied">Replied</option>
                        <option value="Interested">Interested</option>
                        <option value="Collaboration Confirmed">Collaboration Confirmed</option>
                        <option value="Not Interested">Not Interested</option>
                        <option value="Opted Out">Opted Out</option>
                      </select>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5 opacity-80 group-hover:opacity-100">
                        {inf.email && (
                          <button
                            onClick={() => handleGenerateSingle(inf)}
                            title="Generate Cold Email"
                            className="p-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600 text-purple-300 hover:text-white transition-colors"
                          >
                            <Send className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button
                          onClick={() => openEditModal(inf)}
                          title="Edit Details / Notes"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(inf.id)}
                          title="Delete Lead"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-900/50 text-slate-400 hover:text-rose-300 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Creator Modal */}
      {isEditing && selectedInf && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-base text-white">
                Edit Lead: {selectedInf.name} (@{selectedInf.username})
              </h3>
              <button
                onClick={() => setIsEditing(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Email Address</label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  placeholder="creator@brand.com"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">CRM Status</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="New Lead">New Lead</option>
                  <option value="Email Available">Email Available</option>
                  <option value="Email Sent">Email Sent</option>
                  <option value="Follow-up Due">Follow-up Due</option>
                  <option value="Replied">Replied</option>
                  <option value="Interested">Interested</option>
                  <option value="Collaboration Confirmed">Collaboration Confirmed</option>
                  <option value="Not Interested">Not Interested</option>
                  <option value="Opted Out">Opted Out</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">CRM Notes</label>
                <textarea
                  rows={3}
                  value={editForm.notes}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  placeholder="Notes about rates, shipping, or communication history..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={saveEdit}
                className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/30"
              >
                Save & Sync
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InfluencerTable;
