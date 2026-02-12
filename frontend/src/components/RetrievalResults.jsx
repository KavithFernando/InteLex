import { useState } from 'react';

export default function RetrievalResults({ results, onSelectCase }) {
  const [hoverId, setHoverId] = useState(null);

  if (!results?.length) return null;

  return (
    <div className="py-2 px-6">
      <div className="max-w-full mx-auto">
        <div className="flex gap-3 items-start">
          
          {/* Retrieved cases container */}
          <div className="max-w-[80%] py-3 px-4 rounded-bl-md bg-surface border border-border">
            <h3 className="m-0 mb-3 text-[0.85rem] font-semibold text-content-secondary">
              Retrieved cases
            </h3>
            <ul className="list-none m-0 p-0 flex flex-wrap gap-2">
              {results.map((c) => {
                const isHover = hoverId === c.case_id;
                return (
                  <li key={c.case_id}>
                    <button
                      type="button"
                      onClick={() => onSelectCase(c.case_id)}
                      onMouseEnter={() => setHoverId(c.case_id)}
                      onMouseLeave={() => setHoverId(null)}
                      className={`flex flex-col items-start py-2.5 px-3.5 rounded-lg text-[0.85rem] text-left cursor-pointer border transition-colors ${
                        isHover ? 'border-accent bg-accent-light' : 'border-border bg-main-bg'
                      } text-content-primary hover:shadow-sm`}
                    >
                      <span className="font-medium mb-1 line-clamp-2">
                        {c.case_title || c.case_id}
                      </span>
                      {c.decision_date && (
                        <span className="text-xs text-content-secondary">{c.decision_date}</span>
                      )}
                      {c.score != null && (
                        <span className="text-xs text-content-secondary">
                          Score: {typeof c.score === 'number' ? c.score.toFixed(2) : c.score}
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}