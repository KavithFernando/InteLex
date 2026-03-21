import { useState } from 'react';
import ChangePasswordModal from './ChangePasswordModal';

function formatDate(iso) {
  if (!iso) return 'New chat';
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function UserSection({ user, onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);

  const initials = user.username.slice(0, 2).toUpperCase();

  return (
    <>
      {showChangePassword && (
        <ChangePasswordModal onClose={() => setShowChangePassword(false)} />
      )}

      <div className="p-3 border-t border-sidebar-border/50 bg-sidebar-bg relative">
        <button
          type="button"
          onClick={() => setMenuOpen((o) => !o)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-sidebar-hover cursor-pointer transition-colors group border border-transparent hover:border-sidebar-border/50"
        >
          <div className="w-8 h-8 rounded-full bg-indigo-gradient flex items-center justify-center text-white ring-1 ring-accent/20 group-hover:ring-accent/50 group-hover:shadow-glow-sm transition-all shrink-0">
            <span className="text-xs font-bold">{initials}</span>
          </div>
          <div className="flex-1 min-w-0 text-left">
            <p className="text-sm font-medium text-white/90 truncate group-hover:text-white">{user.username}</p>
            <p className="text-[10px] text-content-muted truncate capitalize">{user.role}</p>
          </div>
          <svg
            className={`w-4 h-4 text-content-muted/60 shrink-0 transition-transform duration-200 ${menuOpen ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </button>

        {menuOpen && (
          <div className="absolute bottom-full left-3 right-3 mb-1 bg-[#1e293b] border border-sidebar-border/70 rounded-xl shadow-xl overflow-hidden z-50">
            <button
              type="button"
              onClick={() => { setMenuOpen(false); setShowChangePassword(true); }}
              className="w-full flex items-center gap-3 px-4 py-3 text-sm text-content-muted hover:text-white hover:bg-sidebar-hover transition-colors"
            >
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              Change Password
            </button>
            <div className="border-t border-sidebar-border/50" />
            <button
              type="button"
              onClick={() => { setMenuOpen(false); onLogout(); }}
              className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
            >
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign Out
            </button>
          </div>
        )}
      </div>
    </>
  );
}

export default function ConversationList({
  conversations,
  currentId,
  onSelect,
  onCreate,
  onDelete,
  loading,
  user,
  onLogout,
  isAdmin,
  onOpenAuditLogs,
  isDark,
  onToggleTheme,
}) {
  const [hoverId, setHoverId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  function handleDeleteClick(e, conversationId) {
    e.stopPropagation();
    setConfirmDeleteId(conversationId);
  }

  function handleConfirmDelete(e, conversationId) {
    e.stopPropagation();
    setConfirmDeleteId(null);
    onDelete(conversationId);
  }

  function handleCancelDelete(e) {
    e.stopPropagation();
    setConfirmDeleteId(null);
  }

  return (
    <div className="flex flex-col h-full bg-sidebar-bg text-content-inverse">
      {/* Logo Section */}
      <div className="flex items-center gap-3 px-5 py-6 border-b border-sidebar-border/50">
        <div className="w-12 h-12 rounded-2xl bg-indigo-gradient flex items-center justify-center shadow-glow-sm shrink-0">
          <img
            src="../../public/images/logo_white.png"
            alt="InteLex Logo"
            className="w-8 h-8 object-contain drop-shadow-md"
          />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-white text-3xl font-serif font-bold tracking-tight">InteLex</h1>
        </div>
        {/* Theme toggle */}
        <button
          type="button"
          onClick={onToggleTheme}
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
        >
          {isDark ? (
            /* Sun icon */
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <circle cx="12" cy="12" r="5" />
              <path strokeLinecap="round" d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
            </svg>
          ) : (
            /* Moon icon */
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
            </svg>
          )}
        </button>
      </div>

      <div className="p-4 px-3 space-y-2">
        <button
          onClick={onCreate}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-indigo-gradient hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 px-4 rounded-xl transition-all duration-200 shadow-glow-sm hover:shadow-glow font-medium group"
        >
          <svg className="w-5 h-5 transition-transform group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span className="tracking-wide text-sm">New Conversation</span>
        </button>
        {isAdmin && onOpenAuditLogs && (
          <button
            type="button"
            onClick={onOpenAuditLogs}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-sidebar-border/70 bg-sidebar-hover/50 hover:bg-sidebar-hover text-white/90 hover:text-white text-sm font-medium transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            Audit logs
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 px-2 pb-2 scrollbar-hide">
        {loading && conversations.length === 0 ? (
          <div className="text-center py-8 text-content-muted text-sm px-4">
            <div className="w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin mx-auto mb-3" />
            Loading conversations...
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-8 text-content-muted text-sm px-4">
            No conversations yet. Start a new one!
          </div>
        ) : (
          <div className="space-y-1">
            <h3 className="px-3 py-2 text-[10px] font-bold text-content-muted/70 uppercase tracking-wider mb-1 mt-2">Recents</h3>
            {conversations.map((conv) => {
              const isActive = conv.conversation_id === currentId;
              const isHovered = hoverId === conv.conversation_id;
              const isConfirming = confirmDeleteId === conv.conversation_id;

              return (
                <div
                  key={conv.conversation_id}
                  className={`relative rounded-lg transition-all duration-200 border border-transparent ${
                    isActive
                      ? 'bg-sidebar-active border-sidebar-border/50 shadow-sm'
                      : 'hover:bg-sidebar-hover'
                  }`}
                  onMouseEnter={() => setHoverId(conv.conversation_id)}
                  onMouseLeave={() => { setHoverId(null); }}
                >
                  {/* Confirmation overlay */}
                  {isConfirming && (
                    <div className="absolute inset-0 z-10 rounded-lg bg-[#1e293b] border border-red-500/30 flex items-center justify-between px-3 gap-2">
                      <span className="text-xs text-white/90 truncate">Delete this chat?</span>
                      <div className="flex gap-1.5 shrink-0">
                        <button
                          type="button"
                          onClick={(e) => handleConfirmDelete(e, conv.conversation_id)}
                          className="px-2.5 py-1 rounded-md bg-red-500 hover:bg-red-400 text-white text-xs font-medium transition-colors"
                        >
                          Delete
                        </button>
                        <button
                          type="button"
                          onClick={handleCancelDelete}
                          className="px-2.5 py-1 rounded-md bg-sidebar-hover hover:bg-sidebar-active text-white/70 hover:text-white text-xs font-medium transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Select button — the main clickable content */}
                  <button
                    type="button"
                    onClick={() => onSelect(conv.conversation_id)}
                    className={`w-full text-left p-3 rounded-lg pr-8 ${
                      isActive ? 'text-white' : 'text-content-muted hover:text-white'
                    }`}
                  >
                    <div className="font-medium truncate text-sm w-full flex items-center gap-2">
                      <svg
                        className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-accent' : 'text-content-muted/50'}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <span className="truncate">{conv.title || 'New Chat'}</span>
                    </div>
                    <div className={`text-[10px] truncate mt-1.5 pl-5.5 font-medium ${isActive ? 'text-accent-light/70' : 'text-content-muted/60'}`}>
                      {formatDate(conv.updated_at || conv.created_at)}
                    </div>
                    {isActive && (
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-indigo-gradient rounded-r-full shadow-glow-sm" />
                    )}
                  </button>

                  {/* Delete button — shown on hover, sibling to select button */}
                  {(isHovered || isActive) && !isConfirming && (
                    <button
                      type="button"
                      onClick={(e) => handleDeleteClick(e, conv.conversation_id)}
                      title="Delete conversation"
                      className="absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-md text-content-muted/50 hover:text-red-400 hover:bg-red-500/10 transition-colors z-10"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {user && <UserSection user={user} onLogout={onLogout} />}
    </div>
  );
}
