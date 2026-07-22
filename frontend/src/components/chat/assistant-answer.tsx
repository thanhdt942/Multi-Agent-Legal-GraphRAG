"use client";

import { CheckCircle, Copy, FileText, WarningCircle } from "@phosphor-icons/react";
import { useState } from "react";

import { AgentTimeline } from "@/components/chat/agent-timeline";
import { CitationMarkdown } from "@/components/citations/citation-markdown";
import type { ChatEntry } from "@/lib/answer-types";

interface AssistantAnswerProps {
  entry: ChatEntry;
  onCitation: (citationId: string) => void;
  onOpenEvidence: () => void;
}

export function AssistantAnswer({ entry, onCitation, onOpenEvidence }: AssistantAnswerProps) {
  const [copied, setCopied] = useState(false);

  async function copyAnswer() {
    try {
      await navigator.clipboard.writeText(entry.answer);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }

  return (
    <article className="answer-card">
      <header className="answer-header">
        <div className="answer-author"><span>§</span><div><strong>Pháp Điển AI</strong><small>{entry.status === "streaming" ? "Đang lập luận" : entry.completion?.abstained ? "Không đủ căn cứ" : "Đã phản biện"}</small></div></div>
        {entry.completion && (
          <span className={`confidence confidence-${entry.completion.confidence.toLowerCase()}`}>
            {entry.completion.confidence}
          </span>
        )}
      </header>

      <AgentTimeline steps={entry.steps} />

      {entry.status === "error" ? (
        <div className="answer-error"><WarningCircle size={20} /><div><strong>Không thể hoàn tất nghiên cứu</strong><p>{entry.error}</p></div></div>
      ) : (
        <div className="legal-prose">
          <CitationMarkdown text={entry.answer} streaming={entry.status === "streaming"} onCitation={onCitation} />
        </div>
      )}

      {entry.status === "done" && (
        <footer className="answer-footer">
          <button type="button" onClick={onOpenEvidence}><FileText size={16} /> {entry.citations.length} nguồn</button>
          <span>{entry.completion?.usage.input_tokens.toLocaleString("vi-VN")} tokens đầu vào</span>
          <button className="copy-action" type="button" onClick={copyAnswer} aria-label="Sao chép câu trả lời">
            {copied ? <CheckCircle size={17} weight="fill" /> : <Copy size={17} />}
          </button>
        </footer>
      )}
    </article>
  );
}
