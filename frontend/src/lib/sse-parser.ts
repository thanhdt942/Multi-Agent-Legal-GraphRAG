import type { SseEvent } from "@/lib/answer-types";

export interface ParsedSseChunk {
  events: SseEvent[];
  remainder: string;
}

function parseBlock(block: string): SseEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const rawLine of block.split(/\r?\n/)) {
    if (rawLine.startsWith("event:")) event = rawLine.slice(6).trim();
    if (rawLine.startsWith("data:")) dataLines.push(rawLine.slice(5).trimStart());
  }
  if (!dataLines.length) return null;
  try {
    return { event, data: JSON.parse(dataLines.join("\n")) } as SseEvent;
  } catch {
    return null;
  }
}

export function parseSseChunk(buffer: string): ParsedSseChunk {
  const blocks = buffer.split(/\r?\n\r?\n/);
  const remainder = blocks.pop() ?? "";
  const events = blocks.map(parseBlock).filter((event): event is SseEvent => event !== null);
  return { events, remainder };
}

export function parseFinalSseBlock(buffer: string): SseEvent | null {
  return buffer.trim() ? parseBlock(buffer) : null;
}
