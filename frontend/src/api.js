/**
 * API client for InteLex backend. Uses /api Vite proxy → http://127.0.0.1:8000.
 * Auth token is stored in localStorage and injected into every request automatically.
 * A 401 response clears the token and fires the 'auth:logout' window event so
 * App.jsx can redirect to the login page without the API needing to know about React state.
 */
const BASE = '/api';
const TOKEN_KEY = 'intelex_token';

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const token = getStoredToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const url = `${BASE}${path}`;
  const res = await fetch(url, { headers, ...options });

  if (!res.ok) {
    const err = new Error(res.statusText);
    err.status = res.status;
    try {
      err.body = await res.json();
    } catch {
      err.body = await res.text();
    }
    if (res.status === 401) {
      clearToken();
      window.dispatchEvent(new Event('auth:logout'));
    }
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

// ---------- Auth ----------

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  storeToken(data.access_token);
  return data;
}

export async function register(username, password) {
  const data = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  storeToken(data.access_token);
  return data;
}

export async function logout() {
  try {
    await request('/auth/logout', { method: 'POST' });
  } finally {
    clearToken();
  }
}

export async function getMe() {
  return request('/auth/me');
}

export async function changePassword(currentPassword, newPassword) {
  return request('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

// ---------- Conversations & Chat ----------

export async function deleteConversation(conversationId) {
  return request(`/conversations/${encodeURIComponent(conversationId)}`, { method: 'DELETE' });
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

// ---------- Cases ----------

export async function getCase(caseId) {
  return request(`/cases/${encodeURIComponent(caseId)}`);
}

// ---------- Admin ----------

export async function listAdminUsers() {
  return request('/admin/users');
}

/**
 * @param {{ user_id?: number, action?: string, since?: string, limit?: number }} params
 */
export async function listAuditLogs(params = {}) {
  const sp = new URLSearchParams();
  if (params.user_id != null) sp.set('user_id', String(params.user_id));
  if (params.action != null) sp.set('action', params.action);
  if (params.since != null) sp.set('since', params.since);
  if (params.limit != null) sp.set('limit', String(params.limit));
  const qs = sp.toString();
  return request(`/admin/audit-logs${qs ? `?${qs}` : ''}`);
}
