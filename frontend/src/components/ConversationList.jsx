import { useState } from 'react';

function formatDate(iso) {
  if (!iso) return 'New chat';
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

export default function ConversationList({ conversations, currentId, onSelect, onCreate, loading }) {
  const [hoverId, setHoverId] = useState(null);

  return (
    <div className="flex flex-col h-full bg-sidebar-bg text-content-inverse">
      {/* Logo Section */}
      <div className="flex items-center gap-3 px-5 py-6 border-b border-sidebar-border/50">
        {/* <div className="w-9 h-9 rounded-xl bg-accent bg-gradient-to-br from-accent to-accent-hover flex items-center justify-center shadow-lg shadow-accent/20">
          <svg className="w-5 h-5 text-accent-fg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div> */}
        <div className="w-12 h-12 rounded-2xl bg-accent border border-[#29323dff] flex items-center justify-center">
          <img
            src="../../public/images/logo_white.png"
            alt="InteLex Logo"
            className="w-8 h-8 object-contain drop-shadow-md"
          />
        </div>
        <div>
          <h1 className="text-surface text-3xl font-serif font-bold tracking-tight">InteLex</h1>
        </div>
      </div>

      <div className="p-4 px-3">
        <button
          onClick={onCreate}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 px-4 rounded-xl transition-all duration-200 shadow-md hover:shadow-lg shadow-accent/20 font-medium group"
        >
          <svg className="w-5 h-5 transition-transform group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span className="tracking-wide text-sm">New Conversation</span>
        </button>
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
              return (
                <button
                  key={conv.conversation_id}
                  onClick={() => onSelect(conv.conversation_id)}
                  onMouseEnter={() => setHoverId(conv.conversation_id)}
                  onMouseLeave={() => setHoverId(null)}
                  className={`w-full text-left p-3 rounded-lg transition-all duration-200 group relative border border-transparent ${isActive
                    ? 'bg-sidebar-active text-white border-sidebar-border/50 shadow-sm'
                    : 'text-content-muted hover:bg-sidebar-hover hover:text-white'
                    }`}
                >
                  <div className="font-medium truncate text-sm pr-2 relative z-10 w-full flex items-center gap-2">
                    <svg className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-accent' : 'text-content-muted/50 group-hover:text-content-muted'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <span className="truncate">{conv.title || 'New Chat'}</span>
                  </div>
                  <div className={`text-[10px] truncate mt-1.5 pl-5.5 relative z-10 font-medium ${isActive ? 'text-accent-light/70' : 'text-content-muted/60 group-hover:text-content-muted/80'}`}>
                    {formatDate(conv.updated_at || conv.created_at)}
                  </div>
                  {isActive && <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-accent rounded-r-full shadow-[0_0_10px_rgba(37,99,235,0.5)]" />}
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="p-4 border-t border-sidebar-border/50 mt-auto bg-sidebar-bg">
        {/* <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-sidebar-hover cursor-pointer transition-colors group border border-transparent hover:border-sidebar-border/50">
          <div className="w-8 h-8 rounded-full bg-surface/5 flex items-center justify-center text-secondary ring-1 ring-white/10 group-hover:ring-accent/40 transition-all">
            <span className="text-xs font-bold">US</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white/90 truncate group-hover:text-white">User Account</p>
            <p className="text-[10px] text-content-muted truncate group-hover:text-accent-light/80">Pro Plan Active</p>
          </div>
        </div> */}
      </div>
    </div>
  );
}