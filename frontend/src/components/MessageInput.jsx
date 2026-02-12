import { useState, useRef, useEffect } from 'react';

export default function MessageInput({ onSend, disabled }) {
  const [value, setValue] = useState('');
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [value]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue('');
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-2 items-end py-4 px-6"
    >
      <textarea
        ref={textareaRef}
        placeholder="Ask about cases or paste legal text..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
          }
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        rows={1}
        disabled={disabled}
        aria-label="Message"
        className={`flex-1 min-h-[2.75rem] max-h-[200px] py-2.5 px-4 rounded-[10px] bg-surface text-content-primary text-[0.95rem] leading-snug resize-none outline-none font-[inherit] disabled:opacity-70 disabled:cursor-not-allowed border ${
          focused ? 'border-accent' : 'border-border'
        }`}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="shrink-0 py-2.5 px-5 border-0 rounded-[10px] bg-accent text-accent-fg text-[0.9rem] font-medium cursor-pointer hover:enabled:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Send
      </button>
    </form>
  );
}
