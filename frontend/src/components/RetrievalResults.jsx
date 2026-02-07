import './RetrievalResults.css';

export default function RetrievalResults({ results, onSelectCase }) {
  if (!results?.length) return null;

  return (
    <div className="retrieval-results">
      <h3 className="retrieval-results-title">Retrieved cases</h3>
      <ul className="retrieval-results-list">
        {results.map((c) => (
          <li key={c.case_id}>
            <button
              type="button"
              className="retrieval-results-item"
              onClick={() => onSelectCase(c.case_id)}
            >
              <span className="retrieval-results-item-title">
                {c.case_title || c.case_id}
              </span>
              {c.decision_date && (
                <span className="retrieval-results-item-date">{c.decision_date}</span>
              )}
              {c.score != null && (
                <span className="retrieval-results-item-score">
                  Score: {typeof c.score === 'number' ? c.score.toFixed(2) : c.score}
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
