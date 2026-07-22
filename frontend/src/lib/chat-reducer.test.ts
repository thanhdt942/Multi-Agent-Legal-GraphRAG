import { describe, expect, it } from "vitest";

import type { AnswerCompletion, Citation } from "@/lib/answer-types";
import { chatReducer, createEntry, createSession, initialChatState } from "@/lib/chat-reducer";

const citation: Citation = {
  citation_id: "cit_01",
  node_id: "article_11",
  document_name: "Luật Đất đai 2024",
  article: "11",
  quote: "Nghiêm cấm hành vi lấn đất, chiếm đất.",
};

const completion: AnswerCompletion = {
  answer_id: "ans_1",
  thread_id: "thread_1",
  confidence: "HIGH",
  abstained: false,
  claims: [{ text: "Lấn đất bị cấm", citation_ids: ["cit_01"], support: "DIRECT" }],
  warnings: [],
  usage: { input_tokens: 10, output_tokens: 5 },
};

describe("chatReducer", () => {
  it("tracks retrieval retry, citations and completion", () => {
    const session = createSession("thread_1");
    const entry = createEntry("entry_1", "Lấn đất có bị cấm không?");
    let state = chatReducer(initialChatState, {
      type: "HYDRATE",
      sessions: [session],
      activeId: session.id,
    });
    state = chatReducer(state, { type: "START_ENTRY", sessionId: session.id, entry });
    state = chatReducer(state, {
      type: "RETRIEVAL_COMPLETED",
      entryId: entry.id,
      citationCount: 1,
    });
    state = chatReducer(state, {
      type: "RETRIEVAL_COMPLETED",
      entryId: entry.id,
      citationCount: 2,
    });
    state = chatReducer(state, { type: "ADD_CITATION", entryId: entry.id, citation });
    state = chatReducer(state, {
      type: "ADD_DELTA",
      entryId: entry.id,
      text: "Lấn đất bị nghiêm cấm [cit_01].",
    });
    state = chatReducer(state, { type: "COMPLETE", entryId: entry.id, completion });

    const result = state.sessions[0].entries[0];
    expect(result.retrievalCount).toBe(2);
    expect(result.steps.find((step) => step.agent === "retrieve_graph_evidence")?.label).toContain(
      "bổ sung",
    );
    expect(result.citations).toEqual([citation]);
    expect(result.answer).toContain("cit_01");
    expect(result.status).toBe("done");
  });
});
