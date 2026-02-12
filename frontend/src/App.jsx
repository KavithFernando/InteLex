import { useState, useEffect, useCallback } from 'react';
import {
  listConversations,
  createConversation,
  getConversationMessages,
  sendMessage as apiSendMessage,
  getCase,
} from './api';
import ConversationList from './components/ConversationList';
import ChatMessage from './components/ChatMessage';
import LoadingMessage from './components/LoadingMessage';
import MessageInput from './components/MessageInput';
import RetrievalResults from './components/RetrievalResults';
import CaseDetailPanel from './components/CaseDetailPanel';

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [caseDetail, setCaseDetail] = useState(null);
  const [caseDetailLoading, setCaseDetailLoading] = useState(false);

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
    refreshConversations();
  }, [refreshConversations]);

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
    setCaseDetail(null);
  }, []);

  const handleSendMessage = useCallback(
    async (text) => {
      const cid = currentConversationId;
      if (!cid) return;

      setMessages((prev) => [
        ...prev,
        { role: 'user', content: text },
      ]);

      setSending(true);
      try {
        const res = await apiSendMessage(cid, text);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: res.response, retrieval_result: res.retrieval_result ?? [] },
        ]);
        // Refresh conversations list to show updated title if this was the first message
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

  const handleSelectCase = useCallback(async (caseId) => {
    setSelectedCaseId(caseId);
    setCaseDetailLoading(true);
    setCaseDetail(null);
    try {
      const detail = await getCase(caseId);
      setCaseDetail(detail);
    } catch (err) {
      console.error('Failed to load case', err);
    } finally {
      setCaseDetailLoading(false);
    }
  }, []);

  const handleCloseCaseDetail = useCallback(() => {
    setSelectedCaseId(null);
    setCaseDetail(null);
    setCaseDetailLoading(false);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-main-bg selection:bg-accent/20">
      <aside className="w-[280px] h-screen shrink-0 flex flex-col border-r border-sidebar-border bg-sidebar-bg overflow-hidden transition-all duration-300 ease-in-out">
        <ConversationList
          conversations={conversations}
          currentId={currentConversationId}
          onSelect={handleSelectConversation}
          onCreate={handleCreateConversation}
          loading={loading}
        />
      </aside>

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-hidden relative">
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
          {messages.length === 0 && !currentConversationId && (
            <div className="flex-1 flex flex-col items-center justify-center py-8 px-8 text-center min-h-0 overflow-y-auto">
              {/* <div className="w-32 h-32 rounded-3xl bg-surface-glass backdrop-blur-xl border border-white/50 shadow-glass flex items-center justify-center mb-8 animate-fade-in relative z-20"> */}
              <img
                src="../public/images/logo.png"
                alt="InteLex Logo"
                className="w-20 h-20 object-contain drop-shadow-md"
              />
              {/* </div> */}
              <h1 className="m-0 mb-3 text-4xl font-serif font-bold text-content-primary tracking-tight">InteLex</h1>
              <p className="m-0 text-content-secondary max-w-[32rem] text-lg leading-relaxed">
                Your AI-powered legal assistant. Start a new chat to analyze cases, find precedents, or draft legal documents with precision.
              </p>
            </div>
          )}
          {messages.length === 0 && currentConversationId && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center py-8 px-8 text-center min-h-0 overflow-y-auto">
              {/* <div className="w-24 h-24 rounded-2xl bg-surface/50 flex items-center justify-center mb-6 shadow-sm border border-border-subtle relative z-20"> */}
              <img
                src="../public/images/logo.png"
                alt="InteLex Logo"
                className="w-14 h-14 object-contain opacity-90"
              />
              {/* </div> */}
              <h2 className="m-0 mb-2 text-2xl font-serif font-semibold text-content-primary">Ready to assist</h2>
              <p className="m-0 text-content-secondary max-w-[28rem]">Ask a question about legal cases or paste a document for analysis.</p>
            </div>
          )}
          <div className="flex-1 min-h-0 overflow-y-auto py-6 space-y-6 scrollbar-hide">
            {messages.map((msg, i) => (
              <div key={i} className="max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8">
                <ChatMessage role={msg.role} content={msg.content} />
                {msg.role === 'assistant' && (msg.retrieval_result?.length ?? 0) > 0 && (
                  <RetrievalResults results={msg.retrieval_result} onSelectCase={handleSelectCase} />
                )}
              </div>
            ))}
            {sending && (
              <div className="max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8">
                <LoadingMessage />
              </div>
            )}
          </div>
        </div>
        {currentConversationId && (
          <div className="shrink-0 z-20 p-4 bg-gradient-to-t from-main-bg via-main-bg/90 to-transparent">
            <div className="max-w-4xl mx-auto w-full">
              <MessageInput onSend={handleSendMessage} disabled={sending} />
            </div>
          </div>
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
                className="py-2.5 px-6 border border-border rounded-lg bg-surface hover:bg-surface-hover text-content-primary transition-colors duration-200 font-medium"
                onClick={handleCloseCaseDetail}
              >
                Close Panel
              </button>
            </div>
          )}
          {caseDetail && (
            <CaseDetailPanel caseDetail={caseDetail} onClose={handleCloseCaseDetail} />
          )}
        </aside>
      )}
    </div>
  );
}