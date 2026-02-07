import './CaseDetailPanel.css';

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

  const section = (title, content) => {
    if (content == null || (Array.isArray(content) && content.length === 0)) return null;
    return (
      <section className="case-detail-section">
        <h4 className="case-detail-section-title">{title}</h4>
        <div className="case-detail-section-content">
          {Array.isArray(content)
            ? content.map((item, i) => (
                <div key={i}>
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
    <div className="case-detail-panel">
      <div className="case-detail-panel-header">
        <h2 className="case-detail-panel-title">{case_title || case_id}</h2>
        <button type="button" className="case-detail-panel-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>
      <div className="case-detail-panel-body">
        {(court_name || decision_date) && (
          <p className="case-detail-meta">
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
