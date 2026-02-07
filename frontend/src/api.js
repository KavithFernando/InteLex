/**
 * API client for InteLex backend. Use base URL /api so Vite proxy forwards to backend.
 */
const BASE = '/api';

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = new Error(res.statusText);
    err.status = res.status;
    try {
      err.body = await res.json();
    } catch {
      err.body = await res.text();
    }
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function listConversations() {
  return request('/conversations/');
}

export async function createConversation() {
  return request('/conversations/', { method: 'POST' });
}

export async function getConversationMessages(conversationId) {
  return request(`/conversations/${encodeURIComponent(conversationId)}/messages/`);
}

export async function sendMessage(conversationId, message) {
  return request('/chat/', {
    method: 'POST',
    body: JSON.stringify({ conversation_id: conversationId, message }),
  });
}

export async function getCase(caseId) {
  return request(`/cases/${encodeURIComponent(caseId)}`);
}
