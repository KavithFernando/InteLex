import React, { useState, useEffect } from 'react';

const LOADING_STAGES = [
  "Analyzing legal query...",
  "Searching precedents...",
  "Reviewing case law...",
  "Drafting response..."
];

export default function LoadingMessage() {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % LOADING_STAGES.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="py-2 px-6 animate-fade-in-up">
      <div className="max-w-full mx-auto">
        <div className="flex gap-4 items-start">
          {/* AI Avatar with glow ring */}
          <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm mt-1 bg-surface border border-accent/30 text-accent animate-ai-pulse">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>

          {/* Loading bubble */}
          <div className="flex flex-col gap-1 items-start mt-1">
            <div className="relative px-5 py-3.5 rounded-2xl rounded-tl-sm text-[0.95rem] leading-relaxed shadow-md bg-surface border border-border text-content-primary flex items-center gap-3 overflow-hidden">
              {/* Subtle indigo shimmer sweep */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-accent/8 to-transparent animate-pulse"></div>

              <svg className="w-4 h-4 text-accent animate-spin relative z-10" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="font-mono text-sm text-content-secondary relative z-10 transition-opacity duration-300">
                {LOADING_STAGES[stageIndex]}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
