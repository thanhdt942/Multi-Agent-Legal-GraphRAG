"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface CitationMarkdownProps {
  text: string;
  streaming: boolean;
  onCitation: (citationId: string) => void;
}

function withCitationLinks(text: string): string {
  return text.replace(/\[(cit_[A-Za-z0-9_-]+)\]/g, "[$1](#citation-$1)");
}

export function CitationMarkdown({ text, streaming, onCitation }: CitationMarkdownProps) {
  if (streaming) return <div className="streaming-copy">{text}<span className="stream-caret" /></div>;

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children }) => {
          if (href?.startsWith("#citation-cit_")) {
            const citationId = href.slice("#citation-".length);
            return (
              <button
                type="button"
                className="inline-citation"
                onClick={() => onCitation(citationId)}
                aria-label={`Mở trích dẫn ${citationId}`}
              >
                {citationId.replace("cit_", "")}
              </button>
            );
          }
          return (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          );
        },
      }}
    >
      {withCitationLinks(text)}
    </ReactMarkdown>
  );
}
