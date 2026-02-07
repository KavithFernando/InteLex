import './ChatMessage.css';

export default function ChatMessage({ role, content }) {
  const isUser = role === 'user';
  return (
    <div className={`chat-message ${isUser ? 'chat-message-user' : 'chat-message-assistant'}`}>
      <div className="chat-message-inner">
        {!isUser && <span className="chat-message-avatar">IA</span>}
        <div className="chat-message-content">
          {content}
        </div>
      </div>
    </div>
  );
}
