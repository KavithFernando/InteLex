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
      } catch (err) {
        console.error('Send message failed', err);
      } finally {
        setSending(false);
      }
    },
    [currentConversationId]
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
    <div className="flex h-screen overflow-hidden">
      <aside className="w-[260px] h-screen shrink-0 flex flex-col border-r border-border overflow-hidden">
        <ConversationList
          conversations={conversations}
          currentId={currentConversationId}
          onSelect={handleSelectConversation}
          onCreate={handleCreateConversation}
          loading={loading}
        />
      </aside>

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-hidden">
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          {messages.length === 0 && !currentConversationId && (
            <div className="flex-1 flex flex-col items-center justify-center py-8 px-8 text-center min-h-0 overflow-y-auto">
              <div className="w-20 h-20 rounded-2xl bg-accent/10 flex items-center justify-center mb-5">
                <svg className="w-10 h-10 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
              </div>
              <h1 className="m-0 mb-2 text-[1.75rem] font-semibold text-content-primary">InteLex</h1>
              <p className="m-0 text-content-secondary max-w-[28rem]">Create a new chat to ask about legal cases or paste legal text to find relevant precedents.</p>
            </div>
          )}
          {messages.length === 0 && currentConversationId && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center py-8 px-8 text-center min-h-0 overflow-y-auto">
              <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h2 className="m-0 mb-2 text-lg font-semibold text-content-primary">Start a conversation</h2>
              <p className="m-0 text-content-secondary max-w-[28rem]">Send a message to begin chatting about legal cases or finding relevant precedents.</p>
            </div>
          )}
          <div className="flex-1 min-h-0 overflow-y-auto py-4">
            {messages.map((msg, i) => (
              <div key={i}>
                <ChatMessage role={msg.role} content={msg.content} />
                {msg.role === 'assistant' && (msg.retrieval_result?.length ?? 0) > 0 && (
                  <RetrievalResults results={msg.retrieval_result} onSelectCase={handleSelectCase} />
                )}
              </div>
            ))}
            {sending && <LoadingMessage />}
          </div>
        </div>
        {currentConversationId && (
          <div className="shrink-0 border-t border-border-strong">
            <MessageInput onSend={handleSendMessage} disabled={sending} />
          </div>
        )}
      </main>

      {(selectedCaseId || caseDetailLoading || caseDetail) && (
        <aside className="w-[40vw] h-screen shrink-0 flex flex-col overflow-hidden border-l border-border">
          {caseDetailLoading && !caseDetail && (
            <div className="py-8 px-8 text-center text-content-secondary overflow-y-auto">Loading case…</div>
          )}
          {!caseDetailLoading && selectedCaseId && !caseDetail && (
            <div className="py-8 px-8 text-center text-content-secondary overflow-y-auto">
              <p className="m-0 mb-4">Could not load case.</p>
              <button type="button" className="py-2 px-4 border border-border rounded-lg bg-surface text-content-primary text-[0.9rem]" onClick={handleCloseCaseDetail}>Close</button>
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