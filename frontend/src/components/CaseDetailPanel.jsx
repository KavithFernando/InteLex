import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export default function CaseDetailPanel({ caseDetail, triggeringQuery, onGenerateInterpretation, onGetPdf, onClose }) {
  const [generatedInterpretation, setGeneratedInterpretation] = useState(null);
  const [interpretationLoading, setInterpretationLoading] = useState(false);
  const [interpretationError, setInterpretationError] = useState(null);

  const [showPdf, setShowPdf] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState(null);

  // Revoke blob URL when the modal closes to free memory
  useEffect(() => {
    if (!showPdf && pdfBlobUrl) {
      URL.revokeObjectURL(pdfBlobUrl);
      setPdfBlobUrl(null);
    }
  }, [showPdf]);

  // Also revoke on unmount
  useEffect(() => {
    return () => { if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl); };
  }, [pdfBlobUrl]);

  const canGenerateInterpretation = Boolean(
    triggeringQuery?.trim() && onGenerateInterpretation && caseDetail?.case_id
  );

  const canViewPdf = Boolean(caseDetail?.pdf_relative_path && onGetPdf && caseDetail?.case_id);

  const handleViewPdf = async () => {
    if (!canViewPdf) return;
    setPdfLoading(true);
    setPdfError(null);
    try {
      const blob = await onGetPdf(caseDetail.case_id);
      const url = URL.createObjectURL(blob);
      setPdfBlobUrl(url);
      setShowPdf(true);
    } catch (err) {
      setPdfError(err?.body?.detail ?? err?.message ?? 'Failed to load PDF.');
    } finally {
      setPdfLoading(false);
    }
  };

  const closePdf = () => setShowPdf(false);

  const handleGenerateInterpretation = async () => {
    if (!canGenerateInterpretation) return;
    setInterpretationLoading(true);
    setInterpretationError(null);
    try {
      const { interpretation } = await onGenerateInterpretation(caseDetail.case_id, triggeringQuery, caseDetail.interpretation_frame_id);
      setGeneratedInterpretation(interpretation);
    } catch (err) {
      setInterpretationError(err?.body?.detail ?? err?.message ?? 'Failed to generate interpretation.');
    } finally {
      setInterpretationLoading(false);
    }
  };

  if (!caseDetail) return null;

  const {
    case_id,
    interpretation_frame_id,
    case_identifier,
    case_title,
    court_name,
    decision_date,
    legal_issue,
    petitioner_claim,
    respondent_argument,
    interpretation_summary,
    outcome,
    source,
    source_citation,
    pdf_relative_path,
    full_text,
    judges,
    clauses,
    keywords,
    precedents_cited,
    principles_established,
    article,
    subclause,
    clause_text,
    key_facts,
  } = caseDetail;

  const Section = ({ title, content, isText = false }) => {
    if (content == null || (Array.isArray(content) && content.length === 0)) return null;
    return (
      <section className="mb-8 border-b border-border/50 pb-6 last:border-0 last:pb-0">
        <h4 className="flex items-center gap-2 mb-3 text-xs font-bold uppercase tracking-wider text-accent font-sans">
          {title}
        </h4>
        <div className={`text-[0.95rem] leading-7 text-content-primary ${isText ? 'font-serif' : 'font-sans'}`}>
          {Array.isArray(content)
            ? content.map((item, i) => (
              <div key={i} className="mb-2 last:mb-0">
                {typeof item === 'object' && item?.article != null ? (
                  <div className="bg-surface-hover/60 p-3 rounded-lg border border-border/60">
                    <span className="font-semibold block text-sm mb-1 text-content-primary">{item.article}</span>
                    <span className="text-content-secondary">{item.text}</span>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <span className="text-accent">•</span>
                    <span className="text-content-secondary">{String(item)}</span>
                  </div>
                )}
              </div>
            ))
            : <div className="whitespace-pre-wrap text-content-secondary">{content}</div>}
        </div>
      </section>
    );
  };

  return (
    <>
    <div className="flex flex-col h-full bg-surface shadow-2xl relative">
      {/* Header */}
      <div className="shrink-0 flex items-start justify-between gap-4 py-5 px-6 border-b border-border bg-surface/90 backdrop-blur-md sticky top-0 z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-gradient text-white uppercase tracking-wider">Case Details</span>
            {decision_date && <span className="text-xs text-content-muted font-mono">{decision_date}</span>}
          </div>
          <h2 className="text-xl font-serif font-bold text-content-primary leading-snug">
            {case_title || case_id}
          </h2>
          {case_identifier && (
            <p className="text-xs text-content-muted font-mono mt-1 line-clamp-2" title={case_identifier}>
              {case_identifier}
            </p>
          )}
          {court_name && (
            <p className="text-sm text-content-secondary mt-1 font-medium">{court_name}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {canViewPdf && (
            <button
              type="button"
              onClick={handleViewPdf}
              disabled={pdfLoading}
              className="group flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-surface-hover border border-border text-content-primary shadow-sm hover:border-accent/60 hover:text-accent hover:shadow-glow-sm hover:-translate-y-px disabled:opacity-60 disabled:transform-none transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/30"
            >
              {pdfLoading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Loading…</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <span>View PDF</span>
                </>
              )}
            </button>
          )}
          {pdfError && (
            <span className="text-xs text-error max-w-[160px] truncate" title={pdfError}>{pdfError}</span>
          )}
          {canGenerateInterpretation && (
            <button
              type="button"
              onClick={handleGenerateInterpretation}
              disabled={interpretationLoading}
              className="group flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-indigo-gradient text-white shadow-glow-sm hover:shadow-glow hover:-translate-y-px disabled:shadow-none disabled:transform-none disabled:opacity-60 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/30"
            >
              {interpretationLoading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Generating…</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 text-white/80 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Generate interpretation</span>
                </>
              )}
            </button>
          )}
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-content-muted hover:bg-surface-hover hover:text-content-primary transition-colors focus:outline-none focus:ring-2 focus:ring-accent/20"
            aria-label="Close panel"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-0 py-6 px-8 scrollbar-hide">
        <div className="max-w-3xl mx-auto">
          {(generatedInterpretation != null) && (
            <div className="mb-8 p-6 rounded-xl bg-accent/5 border border-accent/20 shadow-glow-sm transition-all duration-300">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-accent/20">
                <div className="p-1.5 rounded-md bg-indigo-gradient text-white">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-accent font-sans m-0">
                  AI Generated Interpretation
                </h4>
              </div>
              <div className="prose prose-sm md:prose-base max-w-none font-serif text-[0.95rem] leading-relaxed text-content-primary prose-headings:text-content-primary prose-strong:text-accent prose-a:text-accent">
                <ReactMarkdown>{generatedInterpretation}</ReactMarkdown>
              </div>
            </div>
          )}
          {interpretationError && (
            <section className="mb-8 border-b border-border pb-6">
              <p className="text-sm text-error">{interpretationError}</p>
            </section>
          )}
          {interpretation_frame_id != null && (article || clause_text) && (
            <Section title="Matched Constitution Clause" content={[
              { article: `Article ${article || ''} ${subclause ? `${subclause}` : ''}`.trim(), text: clause_text }
            ]} />
          )}
          {interpretation_frame_id != null && (
            <Section title="Key Facts" content={key_facts} />
          )}
          <Section title="Case Summary" content={interpretation_summary} isText />
          <Section title="Legal Issue" content={legal_issue} isText />
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
              <div className="font-serif text-sm leading-relaxed text-content-secondary/80 max-h-96 overflow-y-auto p-4 bg-surface-hover/50 rounded-xl border border-border custom-scrollbar">
                {full_text}
              </div>
            </div>
          )}

          {(source || source_citation) && (
            <div className="mt-4 text-xs text-content-muted text-center font-mono">
              Source: {typeof (source || source_citation) === 'string' ? (source || source_citation) : JSON.stringify(source || source_citation)}
            </div>
          )}
        </div>
      </div>
    </div>

    {/* PDF viewer modal */}
    {showPdf && pdfBlobUrl && (
      <div className="fixed inset-0 z-50 flex flex-col bg-black/95 animate-fade-in">
        {/* Modal header */}
        <div className="shrink-0 flex items-center justify-between gap-4 px-6 py-3 bg-surface border-b border-border">
          <p className="font-serif font-semibold text-content-primary text-sm truncate max-w-[60%]">
            {case_title || case_id}
          </p>
          <div className="flex items-center gap-3">
            <a
              href={pdfBlobUrl}
              download={`${case_identifier || case_id}.pdf`}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-indigo-gradient text-white hover:opacity-90 hover:-translate-y-px transition-all duration-200 shadow-glow-sm hover:shadow-glow"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </a>
            <button
              onClick={closePdf}
              className="p-2 rounded-lg text-content-muted hover:bg-surface-hover hover:text-content-primary transition-colors focus:outline-none focus:ring-2 focus:ring-accent/20"
              aria-label="Close PDF viewer"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* PDF iframe */}
        <iframe
          src={pdfBlobUrl}
          title={`PDF: ${case_title || case_id}`}
          className="flex-1 w-full border-0"
        />
      </div>
    )}
    </>
  );
}
