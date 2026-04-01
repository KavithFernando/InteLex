import { useState, useEffect, useRef, useCallback } from 'react';
import { uploadIngestPdfs, getIngestJob, listIngestJobs } from '../api';

const STATUS_STYLES = {
  queued:  'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  done:    'bg-green-500/15 text-green-400 border-green-500/30',
  failed:  'bg-red-500/15 text-red-400 border-red-500/30',
};

function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${STATUS_STYLES[status] ?? STATUS_STYLES.queued}`}>
      {(status === 'queued' || status === 'running') && (
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      )}
      {status}
    </span>
  );
}

function JobCard({ job, isActive, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left p-3 rounded-xl border transition-colors ${
        isActive
          ? 'border-accent/50 bg-accent/10'
          : 'border-border/60 bg-surface-hover/40 hover:bg-surface-hover'
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-xs text-content-secondary font-mono truncate">{job.job_id}</span>
        <StatusBadge status={job.status} />
      </div>
      <p className="text-sm text-content-primary truncate">
        {job.filenames.length === 1
          ? job.filenames[0]
          : `${job.filenames[0]} + ${job.filenames.length - 1} more`}
      </p>
      <p className="text-xs text-content-secondary mt-0.5">
        {new Date(job.submitted_at).toLocaleString()}
      </p>
    </button>
  );
}

export default function IngestPanel({ onClose }) {
  // Upload form state
  const [files, setFiles] = useState([]);
  const [clauses, setClauses] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Job list
  const [jobs, setJobs] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(true);

  // Active job being polled / viewed
  const [activeJob, setActiveJob] = useState(null);
  const pollRef = useRef(null);
  const logEndRef = useRef(null);

  // ── Helpers ────────────────────────────────────────────────────────────────

  const refreshJobList = useCallback(async () => {
    try {
      const data = await listIngestJobs();
      setJobs(data);
    } catch {
      // non-fatal
    } finally {
      setLoadingJobs(false);
    }
  }, []);

  const startPolling = useCallback((jobId) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const updated = await getIngestJob(jobId);
        setActiveJob(updated);
        setJobs((prev) => {
          const idx = prev.findIndex((j) => j.job_id === jobId);
          if (idx === -1) return [updated, ...prev];
          const next = [...prev];
          next[idx] = updated;
          return next;
        });
        if (updated.status === 'done' || updated.status === 'failed') {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch {
        // keep polling on transient errors
      }
    }, 3000);
  }, []);

  // Autoscroll log to bottom
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activeJob?.log]);

  useEffect(() => {
    refreshJobList();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [refreshJobList]);

  // ── Handlers ───────────────────────────────────────────────────────────────

  function handleFileChange(e) {
    const picked = Array.from(e.target.files).filter((f) => f.name.toLowerCase().endsWith('.pdf'));
    setFiles(picked);
    setUploadError(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!files.length) {
      setUploadError('Please select at least one PDF file.');
      return;
    }
    setUploading(true);
    setUploadError(null);
    try {
      const job = await uploadIngestPdfs(files, clauses);
      setActiveJob(job);
      setJobs((prev) => [job, ...prev]);
      setFiles([]);
      setClauses('');
      startPolling(job.job_id);
    } catch (err) {
      setUploadError(err.body?.detail ?? err.message ?? 'Upload failed.');
    } finally {
      setUploading(false);
    }
  }

  async function handleSelectJob(job) {
    setActiveJob(job);
    if (job.status === 'queued' || job.status === 'running') {
      startPolling(job.job_id);
    } else if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  const isJobRunning = activeJob?.status === 'queued' || activeJob?.status === 'running';

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full bg-surface overflow-hidden">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between gap-4 py-4 px-6 border-b border-border bg-surface/90 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-serif font-semibold text-content-primary">PDF Ingest</h2>
          <button
            type="button"
            onClick={refreshJobList}
            disabled={loadingJobs}
            className="py-1.5 px-3 rounded-lg border border-border bg-surface hover:bg-surface-hover text-content-primary text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {loadingJobs ? 'Loading…' : 'Refresh'}
          </button>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-surface-hover text-content-secondary hover:text-content-primary transition-colors"
          title="Close"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Body: two-column split */}
      <div className="flex-1 min-h-0 flex overflow-hidden">

        {/* Left: Upload form + job history */}
        <div className="w-80 shrink-0 flex flex-col border-r border-border overflow-y-auto scrollbar-hide">

          {/* Upload form */}
          <form onSubmit={handleSubmit} className="p-5 border-b border-border space-y-4">
            <h3 className="text-sm font-semibold text-content-primary">Upload PDFs</h3>

            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-medium text-content-secondary">PDF files</span>
              <label
                htmlFor="ingest-pdf-input"
                className="relative flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border hover:border-accent/50 bg-surface-hover/30 hover:bg-accent/5 transition-colors cursor-pointer min-h-[88px] px-4 py-4"
              >
                <svg className="w-7 h-7 text-content-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {files.length > 0 ? (
                  <p className="text-xs text-content-primary text-center">
                    {files.length === 1 ? files[0].name : `${files.length} files selected`}
                  </p>
                ) : (
                  <p className="text-xs text-content-secondary text-center">Click to select PDFs</p>
                )}
                <input
                  id="ingest-pdf-input"
                  type="file"
                  accept=".pdf,application/pdf"
                  multiple
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-medium text-content-secondary">Clause whitelist</span>
              <input
                type="text"
                value={clauses}
                onChange={(e) => setClauses(e.target.value)}
                placeholder="e.g. 12(1), 14(1)(a)  — blank = all"
                className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-content-primary placeholder:text-content-muted focus:outline-none focus:ring-1 focus:ring-accent/50"
              />
              <p className="text-xs text-content-muted">
                Comma-separated. Leave blank to extract all clauses the model finds.
              </p>
            </label>

            {uploadError && (
              <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                {uploadError}
              </p>
            )}

            <button
              type="submit"
              disabled={uploading || isJobRunning}
              className="w-full flex items-center justify-center gap-2 accent-gradient-bg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed text-white py-2.5 px-4 rounded-xl transition-all duration-200 shadow-glow-sm text-sm font-medium"
            >
              {uploading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Uploading…
                </>
              ) : isJobRunning ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Running…
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Start ingest
                </>
              )}
            </button>
          </form>

          {/* Job history */}
          <div className="flex-1 p-4 space-y-2">
            <h3 className="text-xs font-semibold text-content-secondary uppercase tracking-wider mb-3">Job history</h3>
            {loadingJobs && jobs.length === 0 ? (
              <div className="flex justify-center py-8">
                <div className="w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
              </div>
            ) : jobs.length === 0 ? (
              <p className="text-xs text-content-muted text-center py-8">No jobs yet.</p>
            ) : (
              jobs.map((j) => (
                <JobCard
                  key={j.job_id}
                  job={j}
                  isActive={activeJob?.job_id === j.job_id}
                  onClick={() => handleSelectJob(j)}
                />
              ))
            )}
          </div>
        </div>

        {/* Right: Job detail / log viewer */}
        <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
          {!activeJob ? (
            <div className="flex-1 flex flex-col items-center justify-center text-content-secondary gap-3">
              <svg className="w-12 h-12 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-sm">Upload PDFs or select a past job to view details.</p>
            </div>
          ) : (
            <div className="flex flex-col h-full overflow-hidden">
              {/* Job header */}
              <div className="shrink-0 flex flex-wrap items-center gap-4 px-6 py-4 border-b border-border">
                <StatusBadge status={activeJob.status} />
                <div>
                  <p className="text-sm font-medium text-content-primary">
                    {activeJob.filenames.join(', ')}
                  </p>
                  <p className="text-xs text-content-secondary font-mono">{activeJob.job_id}</p>
                </div>
                {activeJob.clauses?.length > 0 && (
                  <div className="ml-auto">
                    <p className="text-xs text-content-secondary">
                      Clauses: <span className="text-content-primary">{activeJob.clauses.join(', ')}</span>
                    </p>
                  </div>
                )}
              </div>

              {/* Counters */}
              <div className="shrink-0 flex items-center gap-6 px-6 py-3 border-b border-border bg-surface-hover/20">
                <div className="text-center">
                  <p className="text-xl font-bold text-green-400">{activeJob.frames_created}</p>
                  <p className="text-xs text-content-secondary">Frames added</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-yellow-400">{activeJob.frames_skipped}</p>
                  <p className="text-xs text-content-secondary">Skipped</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-red-400">{activeJob.errors}</p>
                  <p className="text-xs text-content-secondary">Errors</p>
                </div>
              </div>

              {/* Error banner */}
              {activeJob.error && (
                <div className="shrink-0 mx-6 mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  <span className="font-semibold">Error: </span>{activeJob.error}
                </div>
              )}

              {/* Live log */}
              <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide px-6 py-4">
                <h4 className="text-xs font-semibold text-content-secondary uppercase tracking-wider mb-3">Pipeline log</h4>
                {activeJob.log.length === 0 ? (
                  <p className="text-xs text-content-muted italic">Waiting for output…</p>
                ) : (
                  <div className="font-mono text-xs text-content-secondary space-y-1">
                    {activeJob.log.map((line, i) => (
                      <p key={i} className="leading-relaxed whitespace-pre-wrap break-all">
                        {line}
                      </p>
                    ))}
                    <div ref={logEndRef} />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
