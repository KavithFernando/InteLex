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
    <form onSubmit={handleSubmit} className="relative w-full max-w-4xl mx-auto">
      <div className="relative flex items-end gap-2 p-2 bg-surface border border-border/70 rounded-3xl shadow-lg ring-1 ring-black/5 focus-within:ring-2 focus-within:border-accent focus-within:ring-accent/20 transition-all duration-300">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a legal question or describe a case..."
          disabled={disabled}
          rows={1}
          className="w-full max-h-[200px] py-3 pl-4 pr-2 bg-transparent border-0 focus:ring-0 resize-none text-content-primary placeholder:text-content-muted scrollbar-hide leading-relaxed"
          style={{ minHeight: '48px' }}
        />
        <button
          type="submit"
          disabled={!text.trim() || disabled}
          className="shrink-0 p-2.5 mb-1 mr-1 rounded-full bg-accent text-white disabled:opacity-50 disabled:bg-gray-200 disabled:text-gray-400 hover:bg-accent-hover transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50 active:scale-95 shadow-md flex items-center justify-center"
        >
          <svg className="w-5 h-5 translate-x-0.5 translate-y-px" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      <div className="text-center mt-2 text-xs text-content-muted/60 font-medium pb-2">
        InteLex AI can make mistakes. Verify important legal information.
      </div>
    </form>
  );
}
