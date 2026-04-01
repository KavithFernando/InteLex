import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  listConversations,
  createConversation,
  deleteConversation,
  getConversationMessages,
  sendMessage as apiSendMessage,
  getCase,
  getFrame,
  generateCaseInterpretation,
  getMe,
  logout as apiLogout,
  getStoredToken,
  getCasePdf,
} from './api';
import AuthPage from './components/AuthPage';
import ConversationList from './components/ConversationList';
import ChatMessage from './components/ChatMessage';
import LoadingMessage from './components/LoadingMessage';
import MessageInput from './components/MessageInput';
import RetrievalResults from './components/RetrievalResults';
import CaseDetailPanel from './components/CaseDetailPanel';
import AuditLogsPanel from './components/AuditLogsPanel';
import IngestPanel from './components/IngestPanel';

export default function App() {
  // ── Theme state ───────────────────────────────────────────────────────────────
  const [isDark, setIsDark] = useState(() => {
    return localStorage.getItem('inteLex-theme') !== 'light';
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.remove('theme-light');
    } else {
      document.documentElement.classList.add('theme-light');
    }
    localStorage.setItem('inteLex-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const toggleTheme = () => setIsDark((prev) => !prev);

  // ── Auth state ──────────────────────────────────────────────────────────────
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true); // true while verifying stored token

  // ── Chat state ───────────────────────────────────────────────────────────────
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  // Scroll to bottom whenever messages load or a new one arrives
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'instant' });
  }, [messages, sending]);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [selectedTriggeringQuery, setSelectedTriggeringQuery] = useState(null);
  const [caseDetail, setCaseDetail] = useState(null);
  const [caseDetailLoading, setCaseDetailLoading] = useState(false);
  const [showAuditLogs, setShowAuditLogs] = useState(false);
  const [showIngestPanel, setShowIngestPanel] = useState(false);

  // ── Verify stored token on mount ─────────────────────────────────────────────
  useEffect(() => {
    if (!getStoredToken()) {
      setAuthLoading(false);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setAuthLoading(false));
  }, []);

  // ── Listen for 401 auto-logout from the API layer ────────────────────────────
  useEffect(() => {
    function handleForcedLogout() {
      setUser(null);
      setConversations([]);
      setCurrentConversationId(null);
      setMessages([]);
      setSelectedCaseId(null);
      setSelectedTriggeringQuery(null);
      setCaseDetail(null);
    }
    window.addEventListener('auth:logout', handleForcedLogout);
    return () => window.removeEventListener('auth:logout', handleForcedLogout);
  }, []);

  // ── Auth handlers ─────────────────────────────────────────────────────────────
  function handleAuthenticated(me) {
    setUser(me);
  }

  async function handleLogout() {
    try {
      await apiLogout();
    } catch {
      // ignore network errors on logout
    }
    setUser(null);
    setConversations([]);
    setCurrentConversationId(null);
    setMessages([]);
    setSelectedCaseId(null);
    setSelectedTriggeringQuery(null);
    setCaseDetail(null);
  }

  // ── Chat handlers ─────────────────────────────────────────────────────────────
  const refreshConversations = useCallback(async () => {
    setLoading(true);
    try {
      const list = await listConversations();
      setConversations(list);
    } catch (err) {
      console.error('Failed to list conversations', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) refreshConversations();
  }, [user, refreshConversations]);

  const loadMessages = useCallback(async (conversationId) => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    setLoading(true);
    try {
      const msgs = await getConversationMessages(conversationId);
      // Map API field pinned_cases → pinned_cases so ChatMessage can render the chips
      setMessages(msgs.map((m) => ({
        ...m,
        pinned_cases: m.pinned_cases ?? undefined,
      })));
    } catch (err) {
      console.error('Failed to load messages', err);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMessages(currentConversationId);
  }, [currentConversationId, loadMessages]);

  const handleCreateConversation = useCallback(async () => {
    setSending(true);
    try {
      const { conversation_id } = await createConversation();
      await refreshConversations();
      setCurrentConversationId(conversation_id);
      setSelectedCaseId(null);
      setSelectedTriggeringQuery(null);
      setCaseDetail(null);
    } catch (err) {
      console.error('Failed to create conversation', err);
    } finally {
      setSending(false);
    }
  }, [refreshConversations]);

  const handleSelectConversation = useCallback((conversationId) => {
    setCurrentConversationId(conversationId);
    setSelectedCaseId(null);
    setSelectedTriggeringQuery(null);
    setCaseDetail(null);
  }, []);

  // All retrieved frames across the entire conversation, deduplicated by frame id.
  // Made available to MessageInput so the user can @-mention them.
  const availableCases = useMemo(() => {
    const seen = new Set();
    return messages
      .filter((m) => m.role === 'assistant' && m.retrieval_result?.length)
      .flatMap((m) => m.retrieval_result)
      .filter(
        (f) =>
          f.interpretation_frame_id != null &&
          !seen.has(f.interpretation_frame_id) &&
          seen.add(f.interpretation_frame_id)
      );
  }, [messages]);

  const handleSendMessage = useCallback(
    async (text, pinnedCases = []) => {
      const cid = currentConversationId;
      if (!cid) return;

      setMessages((prev) => [...prev, { role: 'user', content: text, created_at: new Date().toISOString(), pinned_cases: pinnedCases.length ? pinnedCases : undefined }]);

      setSending(true);
      try {
        const pinnedCaseIds = pinnedCases
          .map((c) => c.interpretation_frame_id)
          .filter((id) => id != null);
        const res = await apiSendMessage(cid, text, pinnedCaseIds);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: res.response, retrieval_result: res.retrieval_result ?? [], created_at: new Date().toISOString(), animateIn: true },
        ]);
        if (messages.length === 0) {
          await refreshConversations();
        }
      } catch (err) {
        console.error('Send message failed', err);
      } finally {
        setSending(false);
      }
    },
    [currentConversationId, messages.length, refreshConversations]
  );

  const handleSelectCase = useCallback(async (caseId, frameId = null, triggeringQuery = null) => {
    setSelectedCaseId(caseId || frameId);
    setSelectedTriggeringQuery(triggeringQuery ?? null);
    setCaseDetailLoading(true);
    setCaseDetail(null);
    try {
      const detail = frameId != null ? await getFrame(frameId) : await getCase(caseId);
      setCaseDetail(detail);
    } catch (err) {
      console.error('Failed to load detail', err);
    } finally {
      setCaseDetailLoading(false);
    }
  }, []);

  const handleDeleteConversation = useCallback(async (conversationId) => {
    try {
      await deleteConversation(conversationId);
      if (currentConversationId === conversationId) {
        setCurrentConversationId(null);
        setMessages([]);
        setSelectedCaseId(null);
        setSelectedTriggeringQuery(null);
        setCaseDetail(null);
      }
      await refreshConversations();
    } catch (err) {
      console.error('Failed to delete conversation', err);
    }
  }, [currentConversationId, refreshConversations]);

  const handleGetPdf = useCallback((caseId) => getCasePdf(caseId), []);

  const handleCloseCaseDetail = useCallback(() => {
    setSelectedCaseId(null);
    setSelectedTriggeringQuery(null);
    setCaseDetail(null);
    setCaseDetailLoading(false);
  }, []);

  // ── Resizable case detail panel ───────────────────────────────────────────────
  const SIDEBAR_WIDTH = 280;   // fixed sidebar width in px
  const PANEL_MIN_PX  = 580;   // narrowest usable panel
  const CHAT_MIN_PX   = 420;   // minimum chat area that must stay visible

  const clampPanelWidth = (w) => {
    const max = Math.max(PANEL_MIN_PX, window.innerWidth - SIDEBAR_WIDTH - CHAT_MIN_PX);
    return Math.max(PANEL_MIN_PX, Math.min(w, max));
  };

  const [panelWidth, setPanelWidth] = useState(() => {
    const stored = localStorage.getItem('inteLex-panel-width');
    const n = stored ? parseInt(stored, 10) : NaN;
    const initial = !isNaN(n) ? n : Math.round(window.innerWidth * 0.42);
    return clampPanelWidth(initial);
  });

  const isDraggingPanel = useRef(false);

  const handlePanelDragStart = useCallback((e) => {
    e.preventDefault();
    isDraggingPanel.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);

  useEffect(() => {
    function onMouseMove(e) {
      if (!isDraggingPanel.current) return;
      const desired = window.innerWidth - e.clientX;
      const max = Math.max(PANEL_MIN_PX, window.innerWidth - SIDEBAR_WIDTH - CHAT_MIN_PX);
      setPanelWidth(Math.max(PANEL_MIN_PX, Math.min(desired, max)));
    }
    function onMouseUp() {
      if (!isDraggingPanel.current) return;
      isDraggingPanel.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      setPanelWidth((prev) => {
        localStorage.setItem('inteLex-panel-width', String(Math.round(prev)));
        return prev;
      });
    }
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, []); // primitive constants + refs — empty dep array is correct here

  // ── Render: loading splash ────────────────────────────────────────────────────
  if (authLoading) {
    return (
      <div className="min-h-screen bg-main-bg flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 aurora-bg opacity-60" />
        <div className="absolute inset-0 grid-overlay" />
        <div className="relative flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
          <p className="text-content-muted text-sm">Loading InteLex…</p>
        </div>
      </div>
    );
  }

  // ── Render: auth page ─────────────────────────────────────────────────────────
  if (!user) {
    return <AuthPage onAuthenticated={handleAuthenticated} />;
  }

  // ── Render: main app ──────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen overflow-hidden bg-main-bg selection:bg-accent/20">
      <aside className="w-[280px] h-screen shrink-0 flex flex-col border-r border-sidebar-border bg-sidebar-bg overflow-hidden transition-all duration-300 ease-in-out">
        <ConversationList
          conversations={conversations}
          currentId={currentConversationId}
          onSelect={handleSelectConversation}
          onCreate={handleCreateConversation}
          onDelete={handleDeleteConversation}
          loading={loading}
          user={user}
          onLogout={handleLogout}
          isAdmin={user?.role === 'admin'}
          onOpenAuditLogs={() => setShowAuditLogs(true)}
          onOpenIngest={() => setShowIngestPanel(true)}
          isDark={isDark}
          onToggleTheme={toggleTheme}
        />
      </aside>

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-hidden relative">
        {showAuditLogs ? (
          <AuditLogsPanel onClose={() => setShowAuditLogs(false)} />
        ) : showIngestPanel ? (
          <IngestPanel onClose={() => setShowIngestPanel(false)} />
        ) : (
          <>
            {/* Animated aurora glow background — always shown; adapts via CSS vars */}
            <div className="absolute inset-0 pointer-events-none z-0 aurora-bg" />
            {/* Subtle dot-grid overlay */}
            <div className="absolute inset-0 pointer-events-none z-0 grid-overlay" />
            {/* Radial vignette */}
            <div className="absolute inset-0 pointer-events-none z-0 bg-gradient-radial from-transparent via-transparent to-main-bg/60" />

            {/* Logo Watermark */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0 overflow-hidden">
              <img
                src="../public/images/logo.png"
                alt=""
                className="w-[480px] h-[480px] object-contain opacity-[0.03] brightness-200"
              />
            </div>

            <div className="flex-1 flex flex-col min-h-0 overflow-hidden relative z-10">
              {messages.length === 0 && !loading && (
                <div className="flex-1 overflow-y-auto scrollbar-hide w-full relative z-10">
                  <div className="min-h-full flex flex-col items-center justify-center px-4 py-8 sm:px-8 w-full max-w-4xl mx-auto animate-fade-in-up">
                    {/* Glowing logo */}
                    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl accent-gradient-bg flex items-center justify-center mb-6 shrink-0 shadow-glow animate-ai-pulse">
                      <img
                        src="../public/images/logo_white.png"
                        alt="InteLex Logo"
                        className="w-10 h-10 sm:w-14 sm:h-14 object-contain"
                      />
                    </div>
                    <h1 className="m-0 mb-3 text-3xl sm:text-4xl font-serif font-bold tracking-tight text-center gradient-text">InteLex AI</h1>
                    <p className="m-0 mb-8 text-content-secondary max-w-[32rem] text-base sm:text-lg leading-relaxed text-center">
                      Your AI-powered legal assistant. Select an example query below or type your own.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full text-left">
                      {[
                        { title: "Equality & State Action (Art. 12)", desc: "I'm revising Article 12(1). How have the courts decided whether discrimination by a public corporation in employment counts as an infringement—especially when the body says its decision was commercial, not government policy?" },
                        { title: "Religious Freedom & Assembly (Art. 10)", desc: "For my essay on Article 10: how have judges treated protests or assemblies in religious precincts when authorities or police intervene? I need examples where the court explains whose rights prevail and on what basis." },
                        { title: "Arrest & Reasons Requirement (Art. 13)", desc: "I'm trying to learn Article 13(1) properly. What do reported cases say about informing a person of the reason for arrest, and how strict is that requirement in the case law we have?" },
                        { title: "Access to Information (Art. 14A)", desc: "For my research note on RTI-style rights: how does our case law treat access to information held by public authorities, and what kinds of restrictions does the court treat as acceptable?" },
                        { title: "Pre-Constitution Laws & Savings Clause (Art. 16)", desc: "I don't fully understand Article 16 in practice. Can you point me to judgments that explain whether pre-Constitution laws can still apply even if they look inconsistent with fundamental rights—and how the court justifies that?" },
                        { title: "Standing & Supreme Court Route (Art. 17)", desc: "As a junior researcher I need clarity on Article 17: who may apply to the Supreme Court for infringement of fundamental rights, and what do cases say \"infringement or imminent infringement\" requires in practice?" }
                      ].map((suggestion, i) => (
                        <button
                          key={i}
                          title={suggestion.desc}
                          disabled={sending}
                          onClick={async () => {
                            if (!currentConversationId) {
                              setSending(true);
                              try {
                                const { conversation_id } = await createConversation();
                                await refreshConversations();
                                setCurrentConversationId(conversation_id);
                                setMessages([{ role: 'user', content: suggestion.desc, created_at: new Date().toISOString() }]);
                                const res = await apiSendMessage(conversation_id, suggestion.desc);
                                setMessages((prev) => [
                                  ...prev,
                                  { role: 'assistant', content: res.response, retrieval_result: res.retrieval_result ?? [], created_at: new Date().toISOString() },
                                ]);
                              } catch (err) {
                                console.error('Failed to create and send', err);
                              } finally {
                                setSending(false);
                              }
                            } else {
                              handleSendMessage(suggestion.desc);
                            }
                          }}
                          className="group flex flex-col items-start p-4 sm:p-5 glass border border-white/5 hover:border-accent/40 rounded-xl hover:shadow-glow-sm transition-all duration-300 active:scale-[0.98] disabled:opacity-50 text-left"
                        >
                          <span className="font-semibold text-content-primary text-sm mb-1.5 flex items-center gap-1.5 group-hover:text-accent transition-colors">
                            {suggestion.title} <span className="text-accent opacity-60 group-hover:opacity-100">&rarr;</span>
                          </span>
                          <span className="text-content-secondary text-xs leading-relaxed line-clamp-2 group-hover:line-clamp-none transition-all duration-300">{suggestion.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {(messages.length > 0 || sending) && (
                <div className="flex-1 min-h-0 overflow-y-auto py-6 space-y-6 scrollbar-hide">
                  {messages.map((msg, i) => (
                    <div key={i} className="max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8">
                      <ChatMessage role={msg.role} content={msg.content} created_at={msg.created_at} isDark={isDark} animateIn={msg.animateIn ?? false} pinnedCases={msg.pinned_cases} />
                      {msg.role === 'assistant' && (msg.retrieval_result?.length ?? 0) > 0 && (
                        <RetrievalResults
                          results={msg.retrieval_result}
                          triggeringUserMessage={messages[i - 1]?.content}
                          onSelectCase={handleSelectCase}
                        />
                      )}
                    </div>
                  ))}
                  {sending && (
                    <div className="max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8">
                      <LoadingMessage />
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
            {currentConversationId && (
              <div className="shrink-0 z-20 p-4 bg-gradient-to-t from-main-bg via-main-bg/95 to-transparent">
                <div className="max-w-4xl mx-auto w-full">
                  <MessageInput onSend={handleSendMessage} disabled={sending} availableCases={availableCases} maxMentions={3} />
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {(selectedCaseId || caseDetailLoading || caseDetail) && (
        <aside
          style={{ width: panelWidth }}
          className="h-screen shrink-0 flex flex-col overflow-hidden border-l border-border bg-surface shadow-2xl z-30 relative"
        >
          {/* Drag-to-resize handle on the left edge */}
          <div
            onMouseDown={handlePanelDragStart}
            title="Drag to resize"
            className="absolute left-0 top-0 bottom-0 w-2 z-40 cursor-col-resize group"
          >
            {/* Thin accent line that glows on hover */}
            <div className="absolute inset-y-0 left-0 w-px bg-border group-hover:bg-accent/50 group-active:bg-accent transition-colors duration-150" />
            {/* Grip dots centred on the handle */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col gap-[4px] opacity-0 group-hover:opacity-100 transition-opacity duration-150">
              {[0,1,2,3,4].map((i) => (
                <div key={i} className="w-[3px] h-[3px] rounded-full bg-accent/60" />
              ))}
            </div>
          </div>

          {caseDetailLoading && !caseDetail && (
            <div className="h-full flex flex-col items-center justify-center text-content-secondary">
              <div className="w-8 h-8 border-2 border-accent/30 border-t-accent rounded-full animate-spin mb-4" />
              <p className="text-sm">Loading case details...</p>
            </div>
          )}
          {!caseDetailLoading && selectedCaseId && !caseDetail && (
            <div className="h-full flex flex-col items-center justify-center text-content-secondary p-8 text-center">
              <p className="mb-6 text-lg">Unable to load case details.</p>
              <button
                type="button"
                className="py-2.5 px-6 border border-border rounded-lg bg-surface hover:bg-surface-hover text-content-primary transition-colors duration-200 font-medium"
                onClick={handleCloseCaseDetail}
              >
                Close Panel
              </button>
            </div>
          )}
          {caseDetail && (
            <CaseDetailPanel
              caseDetail={caseDetail}
              triggeringQuery={selectedTriggeringQuery}
              onGenerateInterpretation={generateCaseInterpretation}
              onClose={handleCloseCaseDetail}
            />
          )}
        </aside>
      )}
    </div>
  );
}
