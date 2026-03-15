import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

function formatTimestamp(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return null;
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  if (isToday) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' }) +
    ', ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function ChatMessage({ role, content, created_at }) {
  const [copied, setCopied] = useState(false);
  const isUser = role === 'user';
  const timestamp = formatTimestamp(created_at);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`group w-full text-left animate-slide-in ${isUser ? 'flex justify-end' : 'flex justify-start'}`}>
      <div className={`flex gap-4 max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm mt-1 transition-transform group-hover:scale-105 ${isUser
          ? 'bg-accent text-white'
          : 'bg-white border border-accent/20 text-accent'
          }`}>
          {isUser ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </div>

        {/* Message bubble + timestamp */}
        <div className={`flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
          <div
            className={`relative px-5 py-3.5 rounded-2xl text-[0.95rem] leading-relaxed shadow-sm transition-all duration-200 ${isUser
              ? 'bg-accent text-white rounded-tr-sm shadow-accent/20'
              : 'bg-white border border-border-subtle/60 text-content-primary rounded-tl-sm shadow-sm'
              }`}
          >
            {isUser ? (
              <div className="whitespace-pre-wrap">{content}</div>
            ) : (
              <div className="prose prose-sm prose-slate max-w-none prose-strong:text-accent prose-strong:font-bold prose-blockquote:border-l-accent prose-blockquote:bg-surface-active/10 prose-blockquote:py-1 prose-blockquote:px-3 prose-blockquote:rounded-r-md prose-blockquote:font-serif prose-blockquote:not-italic prose-blockquote:text-content-secondary prose-a:text-accent hover:prose-a:text-accent-hover text-content-primary">
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            )}
            
            {!isUser && (
               <button
                 onClick={handleCopy}
                 className="absolute top-2 right-2 p-1.5 rounded-md text-content-muted bg-white border border-border opacity-0 group-hover:opacity-100 transition-opacity hover:bg-surface-active/50 hover:text-content-primary shadow-sm"
                 title="Copy to clipboard"
               >
                 {copied ? (
                   <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                   </svg>
                 ) : (
                   <svg className="w-4 h-4 text-content-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                   </svg>
                 )}
               </button>
            )}
          </div>

          {/* Timestamp */}
          {timestamp && (
            <span className="text-[10px] text-content-muted px-1">
              {timestamp}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
