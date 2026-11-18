import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000,
});

export const api = {
  // Health
  getHealth: () => client.get('/health'),

  // Dashboard
  getDashboardStats: () => client.get('/dashboard/stats'),

  // Research
  runResearch: (payload) => client.post('/research', payload),
  uploadCsvResearch: (formData) =>
    client.post('/research/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Influencers
  getInfluencers: (params) => client.get('/influencers', { params }),
  getInfluencer: (id) => client.get(`/influencers/${id}`),
  updateInfluencer: (id, payload) => client.patch(`/influencers/${id}`, null, { params: payload }),
  deleteInfluencer: (id) => client.delete(`/influencers/${id}`),

  // Email Outreach
  generateEmails: (payload) => client.post('/emails/generate', payload),
  getEmailQueue: (status) => client.get('/emails/queue', { params: { status } }),
  getEmailStats: () => client.get('/emails/stats'),
  approveEmail: (id, payload) => client.post(`/emails/approve/${id}`, payload),
  rejectEmail: (id) => client.post(`/emails/reject/${id}`),
  sendApprovedEmails: (payload) => client.post('/emails/send', payload || {}),

  // Follow-ups
  getDueFollowups: () => client.get('/followups/due'),
  generateFollowup: (influencerId) => client.post(`/followups/generate/${influencerId}`),
  triggerFollowupCheck: () => client.post('/followups/trigger-check'),

  // Replies & Inbox
  getReplies: () => client.get('/replies'),
  pollReplies: () => client.post('/replies/poll'),
  simulateReply: (payload) => client.post('/replies/simulate', payload),
  approveReply: (id, payload) => client.post(`/replies/approve/${id}`, payload),
  sendReply: (id) => client.post(`/replies/send/${id}`),
};

export default api;
