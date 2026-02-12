import { useState } from 'react';

export default function CaseDetailPanel({ caseDetail, onClose }) {
  const [closeHover, setCloseHover] = useState(false);

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

  const section = (title, content) => {
    if (content == null || (Array.isArray(content) && content.length === 0)) return null;
    return (
      <section className="mb-5">
        <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-content-secondary">
          {title}
        </h4>
        <div className="text-[0.9rem] leading-normal text-content-primary whitespace-pre-wrap break-words">
          {Array.isArray(content)
            ? content.map((item, i) => (
                <div key={i} className={i > 0 ? 'mt-1.5' : ''}>
                  {typeof item === 'object' && item?.article != null
                    ? `${item.article}: ${item.text ?? ''}`
                    : String(item)}
                </div>
              ))
            : content}
        </div>
      </section>
    );
  };

  return (
    <div className="flex flex-col h-full min-h-0 bg-surface">
      <div className="shrink-0 flex items-start justify-between gap-2 py-4 px-5 border-b border-border-strong">
        <h2 className="m-0 text-base font-semibold text-content-primary leading-tight">
          {case_title || case_id}
        </h2>
        <button
          type="button"
          aria-label="Close"
          onClick={onClose}
          onMouseEnter={() => setCloseHover(true)}
          onMouseLeave={() => setCloseHover(false)}
          className={`shrink-0 w-8 h-8 border-0 rounded-md text-xl leading-none cursor-pointer transition-colors ${
            closeHover ? 'bg-surface-hover text-content-primary' : 'bg-transparent text-content-secondary'
          }`}
        >
          ×
        </button>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto py-4 px-5">
        {(court_name || decision_date) && (
          <p className="m-0 mb-4 text-[0.85rem] text-content-secondary">
            {[court_name, decision_date].filter(Boolean).join(' · ')}
          </p>
        )}
        {section('Legal issue', legal_issue)}
        {section('Petitioner claim', petitioner_claim)}
        {section('Respondent argument', respondent_argument)}
        {section('Interpretation summary', interpretation_summary)}
        {section('Outcome', outcome)}
        {section('Judges', judges)}
        {section('Clauses', clauses)}
        {section('Keywords', keywords)}
        {section('Precedents cited', precedents_cited)}
        {section('Principles established', principles_established)}
        {section('Full text', full_text)}
        {source && section('Source', source)}
      </div>
    </div>
  );
}
