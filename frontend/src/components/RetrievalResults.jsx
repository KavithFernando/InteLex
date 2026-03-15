import { useState } from 'react';

export default function RetrievalResults({ results, triggeringUserMessage, onSelectCase }) {
  if (!results?.length) return null;

  return (
    <div className="mt-4 mb-2 animate-fade-in pl-12 sm:pl-16">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-accent/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <h3 className="text-xs font-bold uppercase tracking-wider text-content-muted font-sans m-0">
          Relevant Cases Found
        </h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {results.map((c) => (
          <button
            key={c.case_id}
            onClick={() => onSelectCase(c.case_id, triggeringUserMessage ?? undefined)}
            className="group flex flex-col items-start text-left bg-surface hover:bg-surface-hover border border-border/80 hover:border-accent/40 rounded-xl p-4 transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.99]"
          >
            <div className="w-full flex justify-between items-start gap-3 mb-2">
              <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-bold bg-accent/5 text-accent border border-accent/10 whitespace-nowrap">
                CASE LAW
              </span>
              {c.score != null && (
                <div className="flex items-center gap-1.5" title={`Relevance Score: ${c.score.toFixed(2)}`}>
                  <div className="h-1 w-8 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-accent text-accent-fg" style={{ width: `${Math.min(c.score * 100, 100)}%` }} />
                  </div>
                </div>
              )}
            </div>

            <h4 className="font-serif font-semibold text-content-primary leading-snug mb-2 line-clamp-2 group-hover:text-accent transition-colors">
              {c.case_title || `Case ${c.case_id}`}
            </h4>

            <div className="mt-auto w-full pt-2 border-t border-border/40 flex justify-between items-center text-xs text-content-muted">
              <span className="font-mono">{c.decision_date || 'Unknown Date'}</span>
              <span className="group-hover:translate-x-1 transition-transform">View Details &rarr;</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}