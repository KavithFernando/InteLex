import { useState, useRef, useEffect } from 'react';

export default function MessageInput({ onSend, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-4xl mx-auto animate-fade-in-up">
      <div className="relative flex items-end gap-2 p-1.5 bg-surface border border-border rounded-[28px] shadow-lg ring-1 ring-accent/5 focus-within:ring-2 focus-within:ring-accent/30 focus-within:border-accent/60 focus-within:shadow-glow-sm hover:border-accent/30 transition-all duration-300">

        {/* Attachment Icon (Visual Only) */}
        <button
          type="button"
          className="shrink-0 p-2.5 mb-1 ml-1 rounded-full text-content-muted hover:bg-surface-hover hover:text-content-primary transition-colors focus:outline-none"
          title="Attach document (Coming Soon)"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a legal question or describe a case..."
          disabled={disabled}
          rows={1}
          className="w-full max-h-[200px] py-3 pl-2 pr-2 bg-transparent border-0 focus:ring-0 focus:outline-none resize-none text-content-primary placeholder:text-content-muted scrollbar-hide leading-relaxed text-[0.95rem]"
          style={{ minHeight: '48px' }}
        />

        {/* Dynamic Send / Stop Button */}
        <button
          type="submit"
          className={`shrink-0 p-2.5 mb-1 mr-1 rounded-full flex items-center justify-center transition-all duration-300 shadow-sm focus:outline-none focus:ring-2 focus:ring-accent/50 active:scale-95 ${
            disabled && !text.trim()
              ? 'bg-surface-active text-content-muted shadow-none'
              : disabled
                ? 'bg-surface-hover hover:bg-surface-active text-content-secondary'
                : 'bg-indigo-gradient hover:opacity-90 text-white shadow-glow-sm hover:shadow-glow'
          }`}
          title={disabled ? "Stop generating" : "Send message"}
        >
          {disabled && text.trim() === '' ? (
             <svg className="w-5 h-5 translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
             </svg>
          ) : disabled ? (
             <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
               <rect x="6" y="6" width="12" height="12" rx="2" />
             </svg>
          ) : (
             <svg className="w-5 h-5 translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
             </svg>
          )}
        </button>
      </div>
      <div className="text-center mt-2.5 text-xs text-content-muted/50 font-medium pb-2 tracking-wide">
        InteLex AI can make mistakes. Verify important legal information.
      </div>
    </form>
  );
}
