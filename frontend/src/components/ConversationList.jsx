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
    <div className="flex flex-col h-full bg-sidebar-bg">
      {/* Logo Section */}
      <div className="flex items-center gap-3 px-4 py-6 border-b border-content-inverse/10">
        <div className="w-9 h-9 rounded-xl bg-accent flex items-center justify-center shadow-lg">
          <svg className="w-5 h-5 text-accent-fg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div>
        <div>
          <h1 className="text-content-inverse font-semibold text-lg tracking-tight">InteLex</h1>
          <p className="text-content-inverse/60 text-xs">AI Assistant</p>
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto py-2 px-2">
        <div className="text-xs font-medium text-content-inverse/50 px-3 py-2 mb-1">
          Recent Conversations
        </div>
        <ul className="list-none m-0 space-y-0.5">
          {conversations.map((c) => {
            const isActive = c.conversation_id === currentId;
            const isHover = hoverId === c.conversation_id && !isActive;
            return (
              <li key={c.conversation_id}>
                <button
                  type="button"
                  onClick={() => onSelect(c.conversation_id)}
                  onMouseEnter={() => setHoverId(c.conversation_id)}
                  onMouseLeave={() => setHoverId(null)}
                  className={`group relative block w-full py-3 px-3 border-0 text-left text-sm cursor-pointer transition-all duration-200 rounded-lg ${
                    isActive
                      ? 'bg-accent text-accent-fg shadow-sm'
                      : isHover
                        ? 'bg-accent/10 text-content-inverse'
                        : 'bg-transparent text-content-inverse/70 hover:text-content-inverse'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <svg className={`w-4 h-4 flex-shrink-0 transition-colors ${isActive ? 'text-accent-fg' : 'text-content-inverse/50 group-hover:text-content-inverse/70'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <span className="block overflow-hidden text-ellipsis whitespace-nowrap flex-1">
                      {formatDate(c.updated_at ?? c.created_at)}
                    </span>
                  </div>
                  {isActive && (
                    <div className="absolute inset-y-0 left-0 w-1 bg-accent rounded-r-full" />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {/* New Chat Button at Bottom */}
      <div className="p-3 border-t border-content-inverse/10">
        <button
          type="button"
          onClick={onCreate}
          disabled={loading}
          className="w-full py-3 px-4 border-0 rounded-xl bg-accent text-accent-fg font-medium text-sm disabled:opacity-60 disabled:cursor-not-allowed hover:enabled:bg-accent-hover transition-all duration-200 hover:enabled:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>New chat</span>
        </button>
      </div>
    </div>
  );
}