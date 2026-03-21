import { useState, useEffect, useCallback } from 'react';
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
} from './api';
import AuthPage from './components/AuthPage';
import ConversationList from './components/ConversationList';
import ChatMessage from './components/ChatMessage';
import LoadingMessage from './components/LoadingMessage';
import MessageInput from './components/MessageInput';
import RetrievalResults from './components/RetrievalResults';
import CaseDetailPanel from './components/CaseDetailPanel';
import AuditLogsPanel from './components/AuditLogsPanel';

export default function App() {
  // ── Auth state ──────────────────────────────────────────────────────────────
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true); // true while verifying stored token

  // ── Chat state ───────────────────────────────────────────────────────────────
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [selectedTriggeringQuery, setSelectedTriggeringQuery] = useState(null);
  const [caseDetail, setCaseDetail] = useState(null);
  const [caseDetailLoading, setCaseDetailLoading] = useState(false);
  const [showAuditLogs, setShowAuditLogs] = useState(false);

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
      setMessages(msgs);
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

  const handleSendMessage = useCallback(
    async (text) => {
      const cid = currentConversationId;
      if (!cid) return;

      setMessages((prev) => [...prev, { role: 'user', content: text, created_at: new Date().toISOString() }]);

      setSending(true);
      try {
        const res = await apiSendMessage(cid, text);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: res.response, retrieval_result: res.retrieval_result ?? [], created_at: new Date().toISOString() },
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

  const handleCloseCaseDetail = useCallback(() => {
    setSelectedCaseId(null);
    setSelectedTriggeringQuery(null);
    setCaseDetail(null);
    setCaseDetailLoading(false);
  }, []);

  // ── Render: loading splash ────────────────────────────────────────────────────
  if (authLoading) {
    return (
      <div className="min-h-screen bg-main-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
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
        />
      </aside>

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-hidden relative">
        {showAuditLogs ? (
          <AuditLogsPanel onClose={() => setShowAuditLogs(false)} />
        ) : (
          <>
            {/* Subtle background glow effect */}
            <div className="absolute inset-0 pointer-events-none bg-gradient-radial from-accent-light/40 to-transparent opacity-50 z-0" />

            {/* Logo Watermark */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0 overflow-hidden">
              <img
                src="../public/images/logo.png"
                alt=""
                className="w-[500px] h-[500px] object-contain opacity-[0.07] grayscale brightness-125"
              />
            </div>

            <div className="flex-1 flex flex-col min-h-0 overflow-hidden relative z-10">
              {messages.length === 0 && !loading && (
                <div className="flex-1 overflow-y-auto scrollbar-hide w-full relative z-10">
                  <div className="min-h-full flex flex-col items-center justify-center px-4 py-8 sm:px-8 w-full max-w-4xl mx-auto animate-fade-in-up">
                    <div className="w-16 h-16 sm:w-20 sm:h-20 bg-white rounded-2xl shadow-sm border border-border-subtle/60 flex items-center justify-center mb-6 shrink-0">
                      <img
                        src="../public/images/logo.png"
                        alt="InteLex Logo"
                        className="w-10 h-10 sm:w-14 sm:h-14 object-contain"
                      />
                    </div>
                    <h1 className="m-0 mb-3 text-3xl sm:text-4xl font-serif font-bold text-content-primary tracking-tight text-center">InteLex AI</h1>
                    <p className="m-0 mb-8 text-content-secondary max-w-[32rem] text-base sm:text-lg leading-relaxed text-center">
                      Your AI-powered legal assistant. Select an example query below or type your own.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full text-left">
                      {[
                        { title: "Optional Retirement", desc: "Can a public corporation refuse to grant an extension of service after an employee reaches the optional retirement age of 55? I need cases on discretionary extension and Article 12." },
                        { title: "Political Discrimination", desc: "Find cases where a public officer was transferred or discriminated against because of political opinion or membership of a local authority." },
                        { title: "Trade Union Action", desc: "I need precedents on probationary public officers whose services were terminated for participating in trade union action or work-to-rule." },
                        { title: "Dealer Agreement Cancellation", desc: "Cases where the Ceylon Petroleum Corporation terminated or cancelled a dealer’s agreement and the dealer challenged it under fundamental rights." },
                        { title: "Arbitrary Promotion Scheme", desc: "Similar cases on denial of promotion or arbitrary promotional criteria for public officers under Article 12." },
                        { title: "Land Alienation", desc: "Cases where the Land Reform Commission alienated land to someone else while rejecting the petitioner’s application." }
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
                          className="group flex flex-col items-start p-4 sm:p-5 bg-white border border-border/80 rounded-xl hover:border-accent hover:shadow-lg transition-all duration-600 active:scale-[0.98] disabled:opacity-50 text-left"
                        >
                          <span className="font-semibold text-content-primary text-sm mb-1.5 flex items-center gap-1.5">
                            {suggestion.title} <span className="text-accent">&rarr;</span>
                          </span>
                          <span className="text-content-secondary text-xs leading-relaxed line-clamp-2 group-hover:line-clamp-none transition-all duration-600" title={suggestion.desc}>{suggestion.desc}</span>
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
                      <ChatMessage role={msg.role} content={msg.content} created_at={msg.created_at} />
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
                </div>
              )}
            </div>
            {currentConversationId && (
              <div className="shrink-0 z-20 p-4 bg-gradient-to-t from-main-bg via-main-bg/90 to-transparent">
                <div className="max-w-4xl mx-auto w-full">
                  <MessageInput onSend={handleSendMessage} disabled={sending} />
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {(selectedCaseId || caseDetailLoading || caseDetail) && (
        <aside className="w-[45vw] h-screen shrink-0 flex flex-col overflow-hidden border-l border-border bg-surface shadow-2xl z-30 transition-shadow">
          {caseDetailLoading && !caseDetail && (
            <div className="h-full flex flex-col items-center justify-center text-content-secondary">
              <div className="w-8 h-8 border-2 border-accent/30 border-t-accent rounded-full animate-spin mb-4" />
              <p>Loading case details...</p>
            </div>
          )}
          {!caseDetailLoading && selectedCaseId && !caseDetail && (
            <div className="h-full flex flex-col items-center justify-center text-content-secondary p-8 text-center">
              <p className="mb-6 text-lg">Unable to load case details.</p>
              <button
                type="button"
                className="py-2.5 px-6 border border-border rounded-lg bg-surface hover:bg-surface-hover text-content-primary transition-colors duration-400 font-medium"
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
