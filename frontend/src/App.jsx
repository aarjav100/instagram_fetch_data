import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import CampaignSetup from './pages/CampaignSetup';
import InfluencerTable from './pages/InfluencerTable';
import EmailApprovalQueue from './pages/EmailApprovalQueue';
import FollowUps from './pages/FollowUps';
import InboxReplies from './pages/InboxReplies';
import { ToastProvider } from './context/ToastContext';
import api from './api';

export function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [counts, setCounts] = useState({ pendingEmails: 0, dueFollowups: 0, replies: 0 });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchGlobalData = async () => {
    setIsRefreshing(true);
    try {
      const [dRes, qRes, fRes, rRes] = await Promise.all([
        api.getDashboardStats().catch(() => ({ data: null })),
        api.getEmailQueue('Pending Approval').catch(() => ({ data: [] })),
        api.getDueFollowups().catch(() => ({ data: [] })),
        api.getReplies().catch(() => ({ data: [] })),
      ]);

      if (dRes.data) setStats(dRes.data);
      setCounts({
        pendingEmails: qRes.data?.length || 0,
        dueFollowups: fRes.data?.length || 0,
        replies: rRes.data?.length || 0,
      });
    } catch (e) {
      console.error('Failed to fetch dashboard data:', e);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchGlobalData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Top Navbar */}
      <Navbar onRefresh={fetchGlobalData} isRefreshing={isRefreshing} />

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          pendingEmailCount={counts.pendingEmails}
          dueFollowupCount={counts.dueFollowups}
          replyCount={counts.replies}
        />

        {/* Dynamic Center Page Content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 bg-slate-950">
          {activeTab === 'dashboard' && (
            <Dashboard
              stats={stats}
              setActiveTab={setActiveTab}
              onRefresh={fetchGlobalData}
            />
          )}

          {activeTab === 'campaign' && (
            <CampaignSetup
              setActiveTab={setActiveTab}
              onRefresh={fetchGlobalData}
            />
          )}

          {activeTab === 'influencers' && (
            <InfluencerTable
              setActiveTab={setActiveTab}
              onRefresh={fetchGlobalData}
            />
          )}

          {activeTab === 'emails' && (
            <EmailApprovalQueue
              onRefresh={fetchGlobalData}
            />
          )}

          {activeTab === 'followups' && (
            <FollowUps
              setActiveTab={setActiveTab}
              onRefresh={fetchGlobalData}
            />
          )}

          {activeTab === 'inbox' && (
            <InboxReplies
              onRefresh={fetchGlobalData}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}
