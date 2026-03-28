import { useState, useRef, useEffect, useMemo } from 'react';
import CaseMentionMenu from './CaseMentionMenu';

// Detect a trailing @ (with optional filter text) at or just before the cursor position.
// Does NOT match mid-word @ like email addresses — only reacts when @ appears after a
// space/newline or at the very start of the input.
const MENTION_RE = /(?:^|[\s\n])@([^@\n]*)$/;

const MENU_SIZE = 8; // max items shown in the dropdown

export default function MessageInput({ onSend, disabled, availableCases = [], maxMentions = 3 }) {
  const [text, setText] = useState('');
  const [pinnedCases, setPinnedCases] = useState([]);
  const [isMentioning, setIsMentioning] = useState(false);
  const [mentionFilter, setMentionFilter] = useState('');
  const [menuActiveIndex, setMenuActiveIndex] = useState(0);
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  // Filtered + deduplicated menu list (derived, not state)
  const filteredCases = useMemo(() => {
    const pinnedIds = new Set(pinnedCases.map((c) => c.interpretation_frame_id));
    const q = mentionFilter.toLowerCase();
    return availableCases
      .filter((f) => !pinnedIds.has(f.interpretation_frame_id))
      .filter((f) => !q || (f.case_title || '').toLowerCase().includes(q))
      .slice(0, MENU_SIZE);
  }, [availableCases, pinnedCases, mentionFilter]);

  const openMention = (filter) => {
    setIsMentioning(true);
    setMentionFilter(filter);
    setMenuActiveIndex(0);
  };

  const closeMention = () => {
    setIsMentioning(false);
    setMentionFilter('');
  };

  const handleTextChange = (e) => {
    const val = e.target.value;
    setText(val);

    // Only open the menu if we haven't hit the pin limit
    if (pinnedCases.length < maxMentions) {
      // Examine text up to current cursor position to avoid reacting to a past @
      const cursor = e.target.selectionStart ?? val.length;
      const beforeCursor = val.slice(0, cursor);
      const match = MENTION_RE.exec(beforeCursor);
      if (match) {
        openMention(match[1]);
        return;
      }
    }
    closeMention();
  };

  const handleMentionSelect = (frame) => {
    // Strip the trailing @{filter} from input text
    setText((prev) => prev.replace(MENTION_RE, (m, p1, offset, str) => {
      // Preserve a leading space/newline if MENTION_RE consumed one
      const leading = m.startsWith('@') ? '' : m[0];
      return leading;
    }));
    setPinnedCases((prev) =>
      prev.find((c) => c.interpretation_frame_id === frame.interpretation_frame_id)
        ? prev
        : [...prev, frame]
    );
    closeMention();
    textareaRef.current?.focus();
  };

  const handleRemovePin = (frameId) => {
    setPinnedCases((prev) => prev.filter((c) => c.interpretation_frame_id !== frameId));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text, pinnedCases);
    setText('');
    setPinnedCases([]);
    closeMention();
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (isMentioning) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setMenuActiveIndex((prev) => Math.min(prev + 1, filteredCases.length - 1));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setMenuActiveIndex((prev) => Math.max(prev - 1, 0));
        return;
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredCases[menuActiveIndex]) handleMentionSelect(filteredCases[menuActiveIndex]);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        closeMention();
        return;
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const atLimit = pinnedCases.length >= maxMentions;
  const hasAvailable = availableCases.length > 0;

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-4xl mx-auto animate-fade-in-up">

      {/* Floating case-mention dropdown */}
      {isMentioning && (
        <CaseMentionMenu
          cases={filteredCases}
          activeIndex={menuActiveIndex}
          onSelect={handleMentionSelect}
          onClose={closeMention}
        />
      )}

      <div className="relative flex flex-col bg-surface border border-border rounded-[28px] shadow-lg ring-1 ring-accent/5 focus-within:ring-2 focus-within:ring-accent/30 focus-within:border-accent/60 focus-within:shadow-glow-sm hover:border-accent/30 transition-all duration-300">

        {/* Pinned case chips */}
        {pinnedCases.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-4 pt-3 pb-1">
            {pinnedCases.map((frame) => (
              <span
                key={frame.interpretation_frame_id}
                className="inline-flex items-center gap-1.5 pl-2 pr-1 py-0.5 rounded-full text-xs font-medium bg-accent/10 text-accent border border-accent/25"
              >
                {frame.matched_article && (
                  <span className="text-[0.6rem] font-bold opacity-70 leading-none">
                    Art.{frame.matched_article}
                  </span>
                )}
                <span className="max-w-[190px] truncate">{frame.case_title || 'Case'}</span>
                <button
                  type="button"
                  onClick={() => handleRemovePin(frame.interpretation_frame_id)}
                  className="shrink-0 w-3.5 h-3.5 flex items-center justify-center rounded-full hover:bg-accent/25 transition-colors"
                  title="Remove reference"
                >
                  <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </span>
            ))}
            {atLimit && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[0.65rem] text-content-muted border border-dashed border-border select-none">
                max {maxMentions} references
              </span>
            )}
          </div>
        )}

        <div className="flex items-end gap-2 p-1.5">
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
            onChange={handleTextChange}
            onKeyDown={handleKeyDown}
            placeholder={
              hasAvailable && !atLimit
                ? 'Ask a legal question… or type @ to reference a retrieved case'
                : 'Ask a legal question or describe a case...'
            }
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
                  : 'accent-gradient-bg hover:opacity-90 text-white shadow-glow-sm hover:shadow-glow'
            }`}
            title={disabled ? 'Stop generating' : 'Send message'}
          >
            {disabled && text.trim() === '' ? (
              /* Empty/idle state — faint arrow */
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14m0 0l-7-7m7 7l-7 7" />
              </svg>
            ) : disabled ? (
              /* Generating — stop square */
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              /* Ready to send — bold arrow */
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 12h14m0 0l-7-7m7 7l-7 7" />
              </svg>
            )}
          </button>
        </div>
      </div>

      <div className="text-center mt-2.5 text-xs text-content-muted/50 font-medium pb-2 tracking-wide">
        InteLex AI can make mistakes. Verify important legal information.
      </div>
    </form>
  );
}
