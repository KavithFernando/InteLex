import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

const WORDS_PER_SECOND = 45; // typing speed
const INTERVAL_MS = Math.round(1000 / WORDS_PER_SECOND);

// Closes any unclosed ** pair so ReactMarkdown never renders raw markers mid-type
function safeMarkdown(text) {
  const parts = text.split('**');
  return parts.length % 2 === 0 ? text + '**' : text;
}

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

export default function ChatMessage({ role, content, created_at, isDark = true, animateIn = false, pinnedCases }) {
  const [copied, setCopied] = useState(false);
  const isUser = role === 'user';
  const timestamp = formatTimestamp(created_at);
  const shouldAnimate = animateIn && !isUser;

  // Streaming state — start empty when animating, full content otherwise
  const [displayed, setDisplayed] = useState(() => shouldAnimate ? '' : content);
  const [isTyping, setIsTyping] = useState(shouldAnimate);
  const wordIndexRef = useRef(0);

  useEffect(() => {
    if (!shouldAnimate) return;

    const words = content.split(' ');
    wordIndexRef.current = 0;
    setDisplayed('');
    setIsTyping(true);

    const timer = setInterval(() => {
      wordIndexRef.current += 1;
      const next = words.slice(0, wordIndexRef.current).join(' ');
      setDisplayed(next);
      if (wordIndexRef.current >= words.length) {
        clearInterval(timer);
        setIsTyping(false);
      }
    }, INTERVAL_MS);

    return () => clearInterval(timer);
  }, [shouldAnimate, content]);

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
          ? 'accent-gradient-bg text-white shadow-glow-sm'
          : 'bg-surface border border-accent/30 text-accent animate-ai-pulse'
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
        <div className={`flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>            {/* Referenced-case chips — shown on user messages that had @-mentions */}
            {isUser && pinnedCases?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 justify-end mb-1">
                {pinnedCases.map((frame) => (
                  <span
                    key={frame.interpretation_frame_id ?? frame.case_title}
                    className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent/10 text-accent border border-accent/30"
                    title={frame.case_title}
                  >
                    {frame.matched_article && (
                      <span className="text-[0.6rem] font-bold opacity-70 leading-none">
                        Art.{frame.matched_article}
                      </span>
                    )}
                    <span className="max-w-[180px] truncate">{frame.case_title || 'Case'}</span>
                  </span>
                ))}
              </div>
            )}          <div
            className={`relative px-5 py-3.5 rounded-2xl text-[0.95rem] leading-relaxed transition-all duration-200 ${isUser
              ? 'accent-bubble-bg text-white rounded-tr-sm shadow-glow-sm'
              : 'bg-surface border border-border text-content-primary rounded-tl-sm shadow-md'
              }`}
          >
            {isUser ? (
              <div className="whitespace-pre-wrap select-text cursor-text">{content}</div>
            ) : isTyping ? (
              /* During streaming: render via markdown with safety-closed markers so case names stay blue */
              <div className={`prose prose-sm max-w-none prose-strong:text-accent prose-strong:font-bold prose-blockquote:border-l-accent prose-blockquote:bg-surface-hover/40 prose-blockquote:py-1 prose-blockquote:px-3 prose-blockquote:rounded-r-md prose-blockquote:font-serif prose-blockquote:not-italic prose-blockquote:text-content-secondary prose-a:text-accent hover:prose-a:text-accent-hover text-content-primary prose-headings:text-content-primary prose-code:text-accent prose-code:bg-surface-active/50 prose-code:rounded prose-code:px-1 ${isDark ? 'prose-invert' : 'prose-slate'}`}>
                <ReactMarkdown>{safeMarkdown(displayed)}</ReactMarkdown>
                <span className="inline-block w-[2px] h-[1em] bg-accent align-middle ml-0.5 animate-pulse" />
              </div>
            ) : (
              /* After streaming (or for history messages): full markdown with bold/blue styling */
              <div className={`prose prose-sm max-w-none prose-strong:text-accent prose-strong:font-bold prose-blockquote:border-l-accent prose-blockquote:bg-surface-hover/40 prose-blockquote:py-1 prose-blockquote:px-3 prose-blockquote:rounded-r-md prose-blockquote:font-serif prose-blockquote:not-italic prose-blockquote:text-content-secondary prose-a:text-accent hover:prose-a:text-accent-hover text-content-primary prose-headings:text-content-primary prose-code:text-accent prose-code:bg-surface-active/50 prose-code:rounded prose-code:px-1 ${isDark ? 'prose-invert' : 'prose-slate'}`}>
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            )}

            {/* Copy button — only shown when message is fully rendered */}
            {!isUser && !isTyping && (
               <button
                 onClick={handleCopy}
                 className="absolute top-2 right-2 p-1.5 rounded-md text-content-muted bg-surface-hover border border-border opacity-0 group-hover:opacity-100 transition-opacity hover:bg-surface-active hover:text-content-primary shadow-sm"
                 title="Copy to clipboard"
               >
                 {copied ? (
                   <svg className="w-4 h-4 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                   </svg>
                 ) : (
                   <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                   </svg>
                 )}
               </button>
            )}
          </div>

          {/* Timestamp — only shown when done typing */}
          {timestamp && !isTyping && (
            <span className="text-[10px] text-content-muted px-1">
              {timestamp}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
