import { useState } from 'react';

export default function CaseDetailPanel({ caseDetail, onClose }) {
  if (!caseDetail) return null;

  const {
    case_id,
    case_title,
    court_name,
    decision_date,
    legal_issue,
    petitioner_claim,
    respondent_argument,
    interpretation_summary,
    outcome,
    source,
    full_text,
    judges,
    clauses,
    keywords,
    precedents_cited,
    principles_established,
  } = caseDetail;

  const Section = ({ title, content, isText = false }) => {
    if (content == null || (Array.isArray(content) && content.length === 0)) return null;
    return (
      <section className="mb-8 border-b border-border-subtle pb-6 last:border-0 last:pb-0">
        <h4 className="flex items-center gap-2 mb-3 text-xs font-bold uppercase tracking-wider text-accent font-sans">
          {title}
        </h4>
        <div className={`text-[0.95rem] leading-7 text-content-primary ${isText ? 'font-serif' : 'font-sans'}`}>
          {Array.isArray(content)
            ? content.map((item, i) => (
              <div key={i} className="mb-2 last:mb-0">
                {typeof item === 'object' && item?.article != null ? (
                  <div className="bg-surface-active/30 p-3 rounded-lg border border-border-subtle">
                    <span className="font-semibold block text-sm mb-1">{item.article}</span>
                    <span className="text-content-secondary">{item.text}</span>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <span className="text-accent">•</span>
                    <span>{String(item)}</span>
                  </div>
                )}
              </div>
            ))
            : <div className="whitespace-pre-wrap">{content}</div>}
        </div>
      </section>
    );
  };

  return (
    <div className="flex flex-col h-full bg-surface shadow-2xl relative">
      {/* Header */}
      <div className="shrink-0 flex items-start justify-between gap-4 py-5 px-6 border-b border-border bg-white/50 backdrop-blur-md sticky top-0 z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-accent text-white uppercase tracking-wider">Case Details</span>
            {decision_date && <span className="text-xs text-content-muted font-mono">{decision_date}</span>}
          </div>
          <h2 className="text-xl font-serif font-bold text-content-primary leading-snug">
            {case_title || case_id}
          </h2>
          {court_name && (
            <p className="text-sm text-content-secondary mt-1 font-medium">{court_name}</p>
          )}
        </div>
        <button
          onClick={onClose}
          className="shrink-0 p-2 rounded-lg text-content-muted hover:bg-surface-hover hover:text-content-primary transition-colors focus:outline-none focus:ring-2 focus:ring-accent/20"
          aria-label="Close panel"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-0 py-6 px-8 scrollbar-hide">
        <div className="max-w-3xl mx-auto">
          <Section title="Legal Issue" content={legal_issue} isText />
          <Section title="Interpretation Summary" content={interpretation_summary} isText />
          <Section title="Outcome" content={outcome} isText />
          <Section title="Petitioner's Claim" content={petitioner_claim} />
          <Section title="Respondent's Argument" content={respondent_argument} />
          <Section title="Key Principles" content={principles_established} />
          <Section title="Precedents Cited" content={precedents_cited} />
          <Section title="Relevant Clauses" content={clauses} />
          <Section title="Judges" content={judges} />
          <Section title="Keywords" content={keywords} />

          {full_text && (
            <div className="mt-8 pt-6 border-t border-border">
              <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-content-muted">Full Text</h4>
              <div className="font-serif text-sm leading-relaxed text-content-secondary/80 max-h-96 overflow-y-auto p-4 bg-surface-hover rounded-xl border border-border-subtle">
                {full_text}
              </div>
            </div>
          )}

          {source && (
            <div className="mt-4 text-xs text-content-muted text-center font-mono">
              Source: {typeof source === 'string' ? source : JSON.stringify(source)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
