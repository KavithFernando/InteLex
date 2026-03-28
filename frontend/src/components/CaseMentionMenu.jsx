import { useEffect, useRef } from 'react';

export default function CaseMentionMenu({ cases, activeIndex, onSelect, onClose }) {
  const menuRef = useRef(null);

  // Scroll the active row into view when navigating with arrow keys
  useEffect(() => {
    if (!menuRef.current) return;
    const active = menuRef.current.querySelector('[data-active="true"]');
    if (active) active.scrollIntoView({ block: 'nearest' });
  }, [activeIndex]);

  // Close when clicking outside
  useEffect(() => {
    function handleOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) onClose();
    }
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [onClose]);

  return (
    <div
      ref={menuRef}
      className="absolute bottom-[calc(100%+8px)] left-0 right-0 bg-surface border border-border rounded-2xl shadow-xl z-50 overflow-hidden"
    >
      <div className="px-3.5 pt-2.5 pb-1 text-[0.65rem] font-semibold uppercase tracking-widest text-content-muted/60 select-none">
        Retrieved Cases — type to filter, ↑↓ to navigate, Enter to select
      </div>

      {cases.length === 0 ? (
        <div className="px-3.5 py-3 text-sm text-content-muted">No matching cases</div>
      ) : (
        <ul className="max-h-52 overflow-y-auto scrollbar-hide py-1">
          {cases.map((frame, i) => (
            <li key={frame.interpretation_frame_id ?? i}>
              <button
                data-active={i === activeIndex ? 'true' : 'false'}
                type="button"
                // mousedown fires before textarea blur — prevent focus loss then select
                onMouseDown={(e) => { e.preventDefault(); onSelect(frame); }}
                className={`w-[calc(100%-8px)] mx-1 flex items-center gap-2.5 px-3 py-2 text-left rounded-xl transition-colors ${
                  i === activeIndex
                    ? 'bg-accent/15 text-content-primary'
                    : 'hover:bg-surface-hover text-content-secondary hover:text-content-primary'
                }`}
              >
                {frame.matched_article && (
                  <span className="shrink-0 inline-flex items-center px-1.5 py-0.5 rounded text-[0.62rem] font-bold bg-accent/20 text-accent border border-accent/30 leading-none">
                    Art.&nbsp;{frame.matched_article}
                  </span>
                )}
                <span className="flex-1 truncate text-sm font-medium">
                  {frame.case_title || 'Untitled Case'}
                </span>
                {frame.decision_date && (
                  <span className="shrink-0 text-xs text-content-muted tabular-nums">
                    {new Date(frame.decision_date).getFullYear()}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
