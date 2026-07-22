"use client";

import { useRef, useState } from "react";

import type { AnswerRequest, SseEvent } from "@/lib/answer-types";
import { parseFinalSseBlock, parseSseChunk } from "@/lib/sse-parser";

export function useAnswerStream() {
  const [streaming, setStreaming] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  async function start(payload: AnswerRequest, onEvent: (event: SseEvent) => void) {
    const controller = new AbortController();
    controllerRef.current = controller;
    setStreaming(true);
    try {
      const response = await fetch("/api/answers/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        let message = `Máy chủ trả về lỗi ${response.status}`;
        try {
          const body = await response.json();
          message = body.error?.message ?? body.message ?? message;
        } catch {
          // Preserve the status-based error when the proxy response is not JSON.
        }
        throw new Error(message);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let remainder = "";
      while (true) {
        const { value, done } = await reader.read();
        remainder += decoder.decode(value ?? new Uint8Array(), { stream: !done });
        const parsed = parseSseChunk(remainder);
        remainder = parsed.remainder;
        parsed.events.forEach(onEvent);
        if (done) break;
      }
      const finalEvent = parseFinalSseBlock(remainder);
      if (finalEvent) onEvent(finalEvent);
    } finally {
      controllerRef.current = null;
      setStreaming(false);
    }
  }

  function stop() {
    controllerRef.current?.abort();
  }

  return { start, stop, streaming };
}
