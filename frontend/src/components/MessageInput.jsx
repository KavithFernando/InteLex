import { useState, useRef, useEffect } from 'react';
import './MessageInput.css';

export default function MessageInput({ onSend, disabled }) {
  const [value, setValue] = useState('');
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
    <form className="message-input-wrap" onSubmit={handleSubmit}>
      <textarea
        ref={textareaRef}
        className="message-input"
        placeholder="Ask about cases or paste legal text..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
          }
        }}
        rows={1}
        disabled={disabled}
        aria-label="Message"
      />
      <button type="submit" className="message-input-send" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  );
}
