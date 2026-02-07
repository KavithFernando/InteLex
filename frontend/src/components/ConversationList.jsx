import './ConversationList.css';

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
  return (
    <div className="conversation-list">
      <button type="button" className="conversation-list-new" onClick={onCreate} disabled={loading}>
        + New chat
      </button>
      <ul className="conversation-list-ul">
        {conversations.map((c) => (
          <li key={c.conversation_id}>
            <button
              type="button"
              className={`conversation-list-item ${c.conversation_id === currentId ? 'active' : ''}`}
              onClick={() => onSelect(c.conversation_id)}
            >
              <span className="conversation-list-item-label">
                {formatDate(c.updated_at ?? c.created_at)}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
