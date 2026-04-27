/**
 * API client for InteLex backend. Uses VITE_API_BASE_URL in deployed builds,
 * or /api locally through the Vite proxy.
 * Auth token is stored in localStorage and injected into every request automatically.
 * A 401 response clears the token and fires the 'auth:logout' window event so
 * App.jsx can redirect to the login page without the API needing to know about React state.
 */
const BASE = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL || '/api').replace(/\/$/, '');
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
  const headers = { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const url = `${BASE}${path}`;
  const res = await fetch(url, { headers, ...options });

  if (!res.ok) {
    const err = new Error(res.statusText);
    err.status = res.status;
    const text = await res.text();
    try {
      err.body = JSON.parse(text);
    } catch {
      err.body = text;
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

export async function sendMessage(conversationId, message, pinnedCaseIds = []) {
  return request('/chat/', {
    method: 'POST',
    body: JSON.stringify({ conversation_id: conversationId, message, pinned_case_ids: pinnedCaseIds }),
  });
}

/**
 * Generate an interpretation of a case in light of the user query that triggered its retrieval.
 * @param {string} caseId - Case ID
 * @param {string} userQuery - The last user message that triggered the LLM to retrieve cases
 * @param {number} [interpretationFrameId] - Optional interpretation frame ID
 * @returns {{ interpretation: string }}
 */
export async function generateCaseInterpretation(caseId, userQuery, interpretationFrameId = null) {
  const body = { case_id: caseId, user_query: userQuery };
  if (interpretationFrameId != null) {
    body.interpretation_frame_id = interpretationFrameId;
  }
  return request('/chat/interpret-case/', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ---------- Cases & Frames ----------

export async function getCase(caseId) {
  return request(`/cases/${encodeURIComponent(caseId)}`);
}

export async function getFrame(frameId) {
  return request(`/frames/${encodeURIComponent(frameId)}`);
}

/**
 * Fetch the PDF for a case as a Blob. Use URL.createObjectURL(blob) to display or download.
 * @param {string} caseId - Internal case id string
 * @returns {Promise<Blob>}
 */
export async function getCasePdf(caseId) {
  const token = getStoredToken();
  const headers = { 'ngrok-skip-browser-warning': 'true' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${BASE}/cases/${encodeURIComponent(caseId)}/pdf`, { headers });
  if (!res.ok) {
    const err = new Error(res.statusText);
    err.status = res.status;
    try { err.body = await res.json(); } catch { err.body = {}; }
    if (res.status === 401) {
      clearToken();
      window.dispatchEvent(new Event('auth:logout'));
    }
    throw err;
  }
  return res.blob();
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

// ---------- Ingest (admin) ----------

/**
 * Upload PDFs for ingest. Starts a background job.
 * @param {File[]} files - Array of File objects from a file input
 * @param {string} [clauses] - Optional comma-separated clause whitelist e.g. "12(1),14(1)(a)"
 * @param {string} [annotatorId] - Annotator label stored in DB (defaults to "admin")
 * @returns {Promise<Object>} IngestJobResponse
 */
export async function uploadIngestPdfs(files, clauses = '', annotatorId = 'admin') {
  const form = new FormData();
  files.forEach((f) => form.append('pdfs', f));
  if (clauses && clauses.trim()) form.append('clauses', clauses.trim());
  form.append('annotator_id', annotatorId);

  const token = getStoredToken();
  const headers = { 'ngrok-skip-browser-warning': 'true' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}/admin/ingest/upload`, {
    method: 'POST',
    headers,
    body: form,
  });

  if (!res.ok) {
    const err = new Error(res.statusText);
    err.status = res.status;
    try { err.body = await res.json(); } catch { err.body = {}; }
    if (res.status === 401) {
      clearToken();
      window.dispatchEvent(new Event('auth:logout'));
    }
    throw err;
  }
  return res.json();
}

/**
 * Poll the status of a specific ingest job.
 * @param {string} jobId
 * @returns {Promise<Object>} IngestJobResponse
 */
export async function getIngestJob(jobId) {
  return request(`/admin/ingest/jobs/${encodeURIComponent(jobId)}`);
}

/**
 * List all ingest jobs, most recent first.
 * @returns {Promise<Object[]>} Array of IngestJobResponse
 */
export async function listIngestJobs() {
  return request('/admin/ingest/jobs');
}
