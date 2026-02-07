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
import MessageInput from './components/MessageInput';
import RetrievalResults from './components/RetrievalResults';
import CaseDetailPanel from './components/CaseDetailPanel';
import './App.css';

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [lastRetrievalResult, setLastRetrievalResult] = useState([]);
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
      setLastRetrievalResult([]);
      return;
    }
    setLoading(true);
    try {
      const msgs = await getConversationMessages(conversationId);
      setMessages(msgs);
      setLastRetrievalResult([]);
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
      setSending(true);
      try {
        const res = await apiSendMessage(cid, text);
        setMessages((prev) => [
          ...prev,
          { role: 'user', content: text },
          { role: 'assistant', content: res.response },
        ]);
        setLastRetrievalResult(res.retrieval_result ?? []);
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
    <div className="app">
      <aside className="app-sidebar">
        <ConversationList
          conversations={conversations}
          currentId={currentConversationId}
          onSelect={handleSelectConversation}
          onCreate={handleCreateConversation}
          loading={loading}
        />
      </aside>

      <main className="app-main">
        <div className="app-chat">
          {messages.length === 0 && !currentConversationId && (
            <div className="app-welcome">
              <h1>InteLex</h1>
              <p>Create a new chat to ask about legal cases or paste legal text to find relevant precedents.</p>
            </div>
          )}
          {messages.length === 0 && currentConversationId && !loading && (
            <div className="app-welcome">
              <p>Send a message to start the conversation.</p>
            </div>
          )}
          <div className="app-messages">
            {messages.map((msg, i) => (
              <div key={i}>
                <ChatMessage role={msg.role} content={msg.content} />
                {msg.role === 'assistant' && i === messages.length - 1 && lastRetrievalResult.length > 0 && (
                  <RetrievalResults results={lastRetrievalResult} onSelectCase={handleSelectCase} />
                )}
              </div>
            ))}
          </div>
          {currentConversationId && (
            <MessageInput onSend={handleSendMessage} disabled={sending} />
          )}
        </div>
      </main>

      {(selectedCaseId || caseDetailLoading || caseDetail) && (
        <aside className="app-case-panel">
          {caseDetailLoading && !caseDetail && (
            <div className="app-case-loading">Loading case…</div>
          )}
          {!caseDetailLoading && selectedCaseId && !caseDetail && (
            <div className="app-case-error">
              <p>Could not load case.</p>
              <button type="button" onClick={handleCloseCaseDetail}>Close</button>
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
