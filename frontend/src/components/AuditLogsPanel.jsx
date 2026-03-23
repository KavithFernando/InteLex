import { useState, useEffect, useCallback } from 'react';
import { listAuditLogs, listAdminUsers } from '../api';

const ACTION_OPTIONS = [
  '',
  'auth.login',
  'auth.login_failed',
  'auth.logout',
  'auth.register',
  'auth.register_failed',
  'auth.change_password',
  'auth.change_password_failed',
  'admin.list_users',
  'chat.create_conversation',
  'chat.delete_conversation',
  'chat.send_message',
  'cases.view',
];

function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString([], { dateStyle: 'short', timeStyle: 'medium' });
}

export default function AuditLogsPanel({ onClose }) {
  const [logs, setLogs] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterUserId, setFilterUserId] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterSince, setFilterSince] = useState('');
  const [limit, setLimit] = useState(100);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { limit: Number(limit) || 100 };
      if (filterUserId) params.user_id = Number(filterUserId);
      if (filterAction) params.action = filterAction;
      if (filterSince) params.since = new Date(filterSince).toISOString();
      const data = await listAuditLogs(params);
      setLogs(data);
    } catch (err) {
      setError(err.body?.detail ?? err.message ?? 'Failed to load audit logs');
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [filterUserId, filterAction, filterSince, limit]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    listAdminUsers()
      .then(setUsers)
      .catch(() => setUsers([]));
  }, []);

  return (
    <div className="flex flex-col h-full bg-surface overflow-hidden">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between gap-4 py-4 px-6 border-b border-border bg-surface/90 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-serif font-semibold text-content-primary">Audit logs</h2>
          <button
            type="button"
            onClick={fetchLogs}
            disabled={loading}
            className="py-1.5 px-3 rounded-lg border border-border bg-surface hover:bg-surface-hover text-content-primary text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-surface-hover text-content-secondary hover:text-content-primary transition-colors"
          title="Close"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Filters */}
      <div className="shrink-0 flex flex-wrap items-end gap-3 py-4 px-6 border-b border-border bg-surface-hover/30">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-content-secondary">User</span>
          <select
            value={filterUserId}
            onChange={(e) => setFilterUserId(e.target.value)}
            className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-content-primary min-w-[140px]"
          >
            <option value="">All users</option>
            {users.map((u) => (
              <option key={u.user_id} value={u.user_id}>
                {u.username} ({u.role})
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-content-secondary">Action</span>
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-content-primary min-w-[180px]"
          >
            {ACTION_OPTIONS.map((a) => (
              <option key={a || 'all'} value={a}>
                {a || 'All actions'}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-content-secondary">Since (date)</span>
          <input
            type="date"
            value={filterSince}
            onChange={(e) => setFilterSince(e.target.value)}
            className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-content-primary"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-content-secondary">Limit</span>
          <input
            type="number"
            min={1}
            max={500}
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-content-primary w-20"
          />
        </label>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-auto p-6">
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-error-light border border-error/30 text-error text-sm">
            {error}
          </div>
        )}
        {loading && logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-content-secondary">
            <div className="w-10 h-10 border-2 border-accent/30 border-t-accent rounded-full animate-spin mb-4" />
            <p>Loading audit logs…</p>
          </div>
        ) : logs.length === 0 ? (
          <p className="text-content-secondary text-center py-16">No audit logs match the filters.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-3 font-semibold text-content-secondary">Time</th>
                  <th className="text-left py-3 px-3 font-semibold text-content-secondary">User</th>
                  <th className="text-left py-3 px-3 font-semibold text-content-secondary">Action</th>
                  <th className="text-left py-3 px-3 font-semibold text-content-secondary">Resource</th>
                  <th className="text-left py-3 px-3 font-semibold text-content-secondary">Success</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-border/70 hover:bg-surface-hover/50">
                    <td className="py-2.5 px-3 text-content-primary whitespace-nowrap">
                      {formatDateTime(log.created_at)}
                    </td>
                    <td className="py-2.5 px-3 text-content-primary">
                      {log.username ?? (log.user_id != null ? `#${log.user_id}` : '—')}
                    </td>
                    <td className="py-2.5 px-3">
                      <code className="text-xs bg-surface-hover px-1.5 py-0.5 rounded text-accent">
                        {log.action}
                      </code>
                    </td>
                    <td className="py-2.5 px-3 text-content-secondary">
                      {log.resource_type && log.resource_id
                        ? `${log.resource_type}: ${log.resource_id}`
                        : log.resource_type ?? '—'}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={
                          log.success
                            ? 'text-success'
                            : 'text-error'
                        }
                      >
                        {log.success ? 'Yes' : 'No'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
