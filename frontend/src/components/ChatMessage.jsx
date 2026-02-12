export default function ChatMessage({ role, content }) {
  const isUser = role === 'user';
  
  return (
    <div className={`py-2 px-6`}>
      <div className="max-w-full mx-auto">
        <div className={`flex gap-3 items-end ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          {/* Avatar */}
          <div className="shrink-0 w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">
            {isUser ? (
              <div className="w-full h-full bg-accent text-accent-fg flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            ) : (
              <div className="w-full h-full bg-message-ai text-accent-fg flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
            )}
          </div>
          
          {/* Message bubble */}
          <div
            className={`max-w-[70%] py-2.5 px-4 rounded-2xl whitespace-pre-wrap break-words leading-normal text-[0.95rem] ${
              isUser
                ? 'bg-accent text-accent-fg rounded-br-md'
                : 'bg-surface text-content-primary border border-border rounded-bl-md'
            }`}
          >
            {content}
          </div>
        </div>
      </div>
    </div>
  );
}