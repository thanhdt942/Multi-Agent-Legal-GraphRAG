import { describe, expect, it } from "vitest";

import { parseFinalSseBlock, parseSseChunk } from "@/lib/sse-parser";

describe("parseSseChunk", () => {
  it("preserves an event split across network chunks", () => {
    const first = parseSseChunk(
      'event: retrieval.completed\ndata: {"retrieval_id":"ret_1","citation_count":2}\n\nevent: answer.delta\ndata: {"text":"Theo',
    );
    expect(first.events).toEqual([
      {
        event: "retrieval.completed",
        data: { retrieval_id: "ret_1", citation_count: 2 },
      },
    ]);

    const second = parseSseChunk(`${first.remainder} luật"}\n\n`);
    expect(second.events).toEqual([{ event: "answer.delta", data: { text: "Theo luật" } }]);
    expect(second.remainder).toBe("");
  });

  it("parses a final block without a trailing separator", () => {
    expect(
      parseFinalSseBlock('event: error\ndata: {"code":"FAILED","message":"Lỗi","retryable":false}'),
    ).toEqual({ event: "error", data: { code: "FAILED", message: "Lỗi", retryable: false } });
  });
});
