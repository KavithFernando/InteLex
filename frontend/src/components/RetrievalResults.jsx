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
        {results.map((c, idx) => (
          <button
            key={c.interpretation_frame_id || c.frame_identifier || `${c.case_id}-${c.matched_article || ''}-${idx}`}
            onClick={() => onSelectCase(c.case_id, c.interpretation_frame_id, triggeringUserMessage ?? undefined)}
            className="group flex flex-col items-start text-left bg-surface hover:bg-surface-hover border border-border/80 hover:border-accent hover:shadow-lg rounded-xl p-5 transition-all duration-300 active:scale-[0.98] relative overflow-hidden"
          >
            {/* Subtle left border accent on hover */}
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-accent transform -translate-x-full group-hover:translate-x-0 transition-transform duration-300"></div>

            <div className="w-full flex justify-between items-start gap-3 mb-3">
              <span className="flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-bold bg-accent/5 text-accent border border-accent/20 tracking-wide uppercase">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
                Case Law
              </span>
              {c.score != null && (
                <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-surface border border-border text-[10px] font-bold text-content-secondary group-hover:text-accent group-hover:border-accent/40 transition-colors shadow-sm" title={`Relevance Score: ${c.score.toFixed(2)}`}>
                   <span>{(c.score * 100).toFixed(0)}% Match</span>
                   <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                </div>
              )}
            </div>

            <h4 className="font-serif font-semibold text-content-primary text-[0.95rem] leading-snug mb-2 line-clamp-2 group-hover:text-accent transition-colors">
              {c.case_title || `Case ${c.case_id}`}
            </h4>
            {c.matched_article != null && c.matched_article !== '' && (
              <p className="text-[11px] text-accent/90 font-medium mb-1">
                Article {c.matched_article}
                {c.matched_subclause ? `${c.matched_subclause}` : ''}
              </p>
            )}
            {c.matched_clause_text && (
              <p className="text-[11px] text-content-muted line-clamp-2 mb-2 leading-relaxed">
                {c.matched_clause_text}
              </p>
            )}

            <div className="mt-auto w-full pt-3 border-t border-border/40 flex justify-between items-center text-xs text-content-muted">
              <span className="font-mono bg-surface-active/30 px-2 py-0.5 rounded text-[10px]">{c.decision_date || 'Unknown Date'}</span>
              <span className="flex items-center gap-1 font-medium group-hover:text-accent transition-colors">
                 View Details
                 <svg className="w-3 h-3 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                 </svg>
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}