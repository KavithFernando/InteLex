export default function LoadingMessage() {
  return (
    <div className="py-2 px-6">
      <div className="max-w-full mx-auto">
        <div className="flex gap-3 items-end">
          {/* Avatar */}
          <div className="shrink-0 w-8 h-8 rounded-full overflow-hidden flex items-center justify-center text-[0.75rem] font-semibold">
            <div className="w-full h-full bg-message-ai text-accent-fg flex items-center justify-center">
              AI
            </div>
          </div>

          {/* Loading bubble */}
          <div className="py-3 px-5 rounded-2xl rounded-bl-md bg-surface border border-border">
            <div className="flex gap-1 items-center">
              <div
                className="w-2 h-2 rounded-full bg-content-secondary animate-bounce"
                style={{ animationDelay: "0ms" }}
              ></div>
              <div
                className="w-2 h-2 rounded-full bg-content-secondary animate-bounce"
                style={{ animationDelay: "150ms" }}
              ></div>
              <div
                className="w-2 h-2 rounded-full bg-content-secondary animate-bounce"
                style={{ animationDelay: "300ms" }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
