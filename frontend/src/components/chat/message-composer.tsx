"use client";

import { ArrowUp, Stop } from "@phosphor-icons/react";
import { useState, type FormEvent, type KeyboardEvent } from "react";

interface MessageComposerProps {
  streaming: boolean;
  disabled: boolean;
  onSubmit: (question: string, compare: boolean) => void;
  onStop: () => void;
}

export function MessageComposer({ streaming, disabled, onSubmit, onStop }: MessageComposerProps) {
  const [question, setQuestion] = useState("");
  const [compare, setCompare] = useState(false);

  function submit(event?: FormEvent) {
    event?.preventDefault();
    if (streaming) {
      onStop();
      return;
    }
    const value = question.trim();
    if (!value || disabled) return;
    onSubmit(value, compare);
    setQuestion("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="composer-dock">
      <form className="research-composer" onSubmit={submit}>
        <label htmlFor="legal-question" className="sr-only">Câu hỏi pháp lý</label>
        <textarea
          id="legal-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Mô tả vấn đề pháp lý cần nghiên cứu..."
          rows={2}
          maxLength={4000}
          disabled={disabled}
        />
        <div className="composer-toolbar">
          <label className="scope-toggle">
            <input
              type="checkbox"
              checked={compare}
              onChange={(event) => setCompare(event.target.checked)}
              disabled={streaming || disabled}
            />
            <span>Đối chiếu Luật 2013</span>
          </label>
          <div className="composer-hint"><kbd>Enter</kbd> gửi · <kbd>Shift Enter</kbd> xuống dòng</div>
          <button
            className={`submit-button ${streaming ? "stop-button" : ""}`}
            type="submit"
            aria-label={streaming ? "Dừng tạo câu trả lời" : "Gửi câu hỏi"}
            disabled={!streaming && (disabled || !question.trim())}
          >
            {streaming ? <Stop size={18} weight="fill" /> : <ArrowUp size={20} weight="bold" />}
          </button>
        </div>
      </form>
      <p className="legal-disclaimer">Thông tin hỗ trợ tra cứu, không thay thế ý kiến chuyên môn pháp lý.</p>
    </div>
  );
}
