import React, { useState } from 'react';
import {
  Sparkles,
  Upload,
  Instagram,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  Users,
  Search,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import api from '../api';
import { useToast } from '../context/ToastContext';

export const CampaignSetup = ({ setActiveTab, onRefresh }) => {
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [csvLoading, setCsvLoading] = useState(false);

  const [formData, setFormData] = useState({
    brand: 'Aura Bloom Skincare',
    campaign: 'Summer Hydration Serum Launch',
    niche: 'Clean Beauty & Skincare',
    keywords: 'clean beauty, glass skin, hydration, cruelty-free',
    location: 'United States',
    min_followers: 10000,
    max_followers: 350000,
    offer_details: 'Free Full Summer Glow Suite ($220 value) + $350 flat fee + 15% recurring affiliate code',
    sender_name: 'Alex Rivera - Head of Partnerships',
    usernames_input: 'skincare_emily, derm_insights, radiant_lifestyle, glowwithkatie',
  });

  const [selectedFile, setSelectedFile] = useState(null);
  const [researchResults, setResearchResults] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleRunResearch = async (e) => {
    e.preventDefault();
    const usernames = formData.usernames_input
      .split(/[\n,]+/)
      .map((u) => u.trim())
      .filter(Boolean);

    if (usernames.length === 0) {
      toast.error('Please enter at least one Instagram username to research.');
      return;
    }

    setLoading(true);
    setResearchResults(null);
    try {
      const payload = {
        brand: formData.brand,
        campaign: formData.campaign,
        niche: formData.niche,
        keywords: formData.keywords,
        location: formData.location,
        min_followers: Number(formData.min_followers) || 0,
        max_followers: Number(formData.max_followers) || 10000000,
        offer_details: formData.offer_details,
        sender_name: formData.sender_name,
        usernames: usernames,
      };

      const res = await api.runResearch(payload);
      setResearchResults(res.data);
      toast.success(`Successfully researched & filtered ${res.data.length} creators!`);
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to complete research. Check API credentials or input.');
    } finally {
      setLoading(false);
    }
  };

  const handleCsvUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      toast.error('Please select a CSV file first.');
      return;
    }

    setCsvLoading(true);
    try {
      const data = new FormData();
      data.append('file', selectedFile);
      data.append('brand', formData.brand);
      data.append('campaign', formData.campaign);

      const res = await api.uploadCsvResearch(data);
      setResearchResults(res.data);
      toast.success(`Imported and evaluated ${res.data.length} creators from CSV!`);
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to import CSV.');
    } finally {
      setCsvLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          Campaign Setup & Influencer Research
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Specify your campaign criteria, then research creator profiles via official Instagram Graph API Business Discovery with Claude filtering.
        </p>
      </div>

      {/* Compliance Notice */}
      <div className="flex items-start gap-3 p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 text-indigo-200 text-xs leading-relaxed">
        <ShieldAlert className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-white">Strict Compliance Guarantee:</strong> We never scrape Instagram. Data is fetched solely through the official Instagram Graph API Business Discovery endpoint or directly uploaded via CSV. Emails are extracted from public creator bios via regex.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Campaign Form */}
        <form onSubmit={handleRunResearch} className="lg:col-span-2 space-y-6 p-7 rounded-3xl bg-slate-900/80 border border-slate-800/80 shadow-xl">
          <div className="flex items-center gap-2 pb-4 border-b border-slate-800 text-sm font-bold text-white">
            <Instagram className="w-4 h-4 text-purple-400" />
            <span>Campaign Parameters</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Brand Name *
              </label>
              <input
                type="text"
                name="brand"
                value={formData.brand}
                onChange={handleChange}
                required
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Campaign Name / Objective *
              </label>
              <input
                type="text"
                name="campaign"
                value={formData.campaign}
                onChange={handleChange}
                required
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Niche / Category
              </label>
              <input
                type="text"
                name="niche"
                value={formData.niche}
                onChange={handleChange}
                placeholder="e.g. Fitness, Clean Beauty, Tech"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Location
              </label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="e.g. United States, UK, Global"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Keywords (comma-separated)
            </label>
            <input
              type="text"
              name="keywords"
              value={formData.keywords}
              onChange={handleChange}
              placeholder="e.g. clean beauty, glass skin, hydration"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Follower Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Min Followers
              </label>
              <input
                type="number"
                name="min_followers"
                value={formData.min_followers}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Max Followers
              </label>
              <input
                type="number"
                name="max_followers"
                value={formData.max_followers}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>
          </div>

          {/* Collaboration Offer */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Collaboration Offer / Perks
            </label>
            <input
              type="text"
              name="offer_details"
              value={formData.offer_details}
              onChange={handleChange}
              placeholder="Free product kit + commission / flat sponsorship fee"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Usernames List */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Target Instagram Usernames *
              </label>
              <span className="text-[11px] text-slate-400">Comma or newline separated</span>
            </div>
            <textarea
              name="usernames_input"
              rows={4}
              value={formData.usernames_input}
              onChange={handleChange}
              placeholder="e.g. username1, username2, @username3"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm font-mono text-purple-200 focus:outline-none focus:border-purple-500 transition-colors resize-none"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-sm shadow-xl shadow-purple-600/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Calling Instagram Graph API & Claude Filtering...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Run Influencer Research</span>
              </>
            )}
          </button>
        </form>

        {/* Fallback CSV Upload Sidecard */}
        <div className="space-y-6">
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800/80 shadow-xl space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-800 text-sm font-bold text-white">
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              <span>CSV Import Fallback</span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Have an existing creator list? Upload a CSV file with columns like: <code className="text-purple-300">username, name, followers, bio, email</code>. Claude will evaluate them against your campaign.
            </p>

            <div className="border-2 border-dashed border-slate-800 hover:border-purple-500/50 rounded-2xl p-6 text-center transition-colors">
              <Upload className="w-8 h-8 text-slate-500 mx-auto mb-2" />
              <input
                type="file"
                accept=".csv"
                id="csv-file-input"
                className="hidden"
                onChange={(e) => setSelectedFile(e.target.files[0])}
              />
              <label
                htmlFor="csv-file-input"
                className="cursor-pointer text-xs font-semibold text-purple-400 hover:text-purple-300 block"
              >
                {selectedFile ? selectedFile.name : 'Choose CSV file to upload'}
              </label>
              <p className="text-[10px] text-slate-500 mt-1">UTF-8 encoded CSV</p>
            </div>

            <button
              onClick={handleCsvUpload}
              disabled={!selectedFile || csvLoading}
              className="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-semibold text-xs border border-slate-700 transition-all flex items-center justify-center gap-2 disabled:opacity-40"
            >
              {csvLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Processing CSV...</span>
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5" />
                  <span>Import & Score CSV</span>
                </>
              )}
            </button>
          </div>

          {/* Quick stats / tips */}
          <div className="p-6 rounded-3xl bg-slate-900/40 border border-slate-800/50 space-y-3 text-xs text-slate-400">
            <h4 className="font-semibold text-white">Best Research Practices</h4>
            <ul className="space-y-2 list-disc list-inside text-[11px] leading-relaxed">
              <li>Target creators between 10K - 250K for optimal ROI & authentic reply rates.</li>
              <li>Include distinct niche keywords to boost Claude's scoring precision.</li>
              <li>Ensure your offer details specify clear value (free kit + paid fee).</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Research Results Preview Drawer/Card */}
      {researchResults && (
        <div className="p-6 rounded-3xl bg-slate-900/90 border border-purple-500/30 shadow-2xl space-y-4 animate-in slide-in-from-bottom-5">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                Research Complete: {researchResults.length} Creators Evaluated
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Saved to local SQLite database and synced to Google Sheets CRM
              </p>
            </div>

            <button
              onClick={() => setActiveTab('influencers')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-all shadow-md shadow-purple-600/30"
            >
              <span>View in Influencer Table</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {researchResults.slice(0, 6).map((inf) => (
              <div
                key={inf.id}
                className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 hover:border-purple-500/30 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <div className="font-bold text-sm text-white">{inf.name}</div>
                      <div className="text-xs text-purple-400 font-mono">@{inf.username}</div>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        inf.relevance_score >= 80
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : inf.relevance_score >= 60
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      Score: {inf.relevance_score}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 line-clamp-2 mt-2 leading-relaxed">
                    {inf.profile_summary || inf.bio}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                  <span>{inf.followers.toLocaleString()} followers</span>
                  <span className={inf.email ? 'text-emerald-400 font-medium' : 'text-slate-500'}>
                    {inf.email ? 'Email Extracted' : 'No public email'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CampaignSetup;
