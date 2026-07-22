import type {
  AgentName,
  AnswerCompletion,
  ChatEntry,
  ChatSession,
  Citation,
} from "@/lib/answer-types";

export interface ChatState {
  sessions: ChatSession[];
  activeId: string;
  hydrated: boolean;
}

export type ChatAction =
  | { type: "HYDRATE"; sessions: ChatSession[]; activeId: string }
  | { type: "NEW_SESSION"; session: ChatSession }
  | { type: "SELECT_SESSION"; sessionId: string }
  | { type: "START_ENTRY"; sessionId: string; entry: ChatEntry }
  | { type: "AGENT_COMPLETED"; entryId: string; agent: AgentName }
  | { type: "RETRIEVAL_COMPLETED"; entryId: string; citationCount: number }
  | { type: "ADD_CITATION"; entryId: string; citation: Citation }
  | { type: "ADD_DELTA"; entryId: string; text: string }
  | { type: "COMPLETE"; entryId: string; completion: AnswerCompletion }
  | { type: "FAIL"; entryId: string; error: string };

export const initialChatState: ChatState = { sessions: [], activeId: "", hydrated: false };

export const AGENT_LABELS: Record<AgentName, string> = {
  analyze_situation: "Phân tích tình huống",
  retrieve_graph_evidence: "Truy xuất đồ thị",
  compare_historical_law: "Đối chiếu lịch sử",
  synthesize_answer: "Tổng hợp lập luận",
  critique_answer: "Phản biện pháp lý",
};

function updateEntry(
  state: ChatState,
  entryId: string,
  updater: (entry: ChatEntry) => ChatEntry,
): ChatState {
  return {
    ...state,
    sessions: state.sessions.map((session) => ({
      ...session,
      entries: session.entries.map((entry) => (entry.id === entryId ? updater(entry) : entry)),
      updatedAt: session.entries.some((entry) => entry.id === entryId)
        ? Date.now()
        : session.updatedAt,
    })),
  };
}

function markStep(entry: ChatEntry, agent: AgentName, label = AGENT_LABELS[agent]): ChatEntry {
  const existing = entry.steps.find((step) => step.agent === agent);
  const steps = entry.steps.map((step) => ({
    ...step,
    status: step.status === "active" ? ("done" as const) : step.status,
  }));
  if (existing) {
    return {
      ...entry,
      steps: steps.map((step) =>
        step.agent === agent ? { ...step, label, status: "done" as const } : step,
      ),
    };
  }
  return { ...entry, steps: [...steps, { agent, label, status: "done" }] };
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "HYDRATE":
      return { sessions: action.sessions, activeId: action.activeId, hydrated: true };
    case "NEW_SESSION":
      return {
        ...state,
        activeId: action.session.id,
        sessions: [action.session, ...state.sessions],
      };
    case "SELECT_SESSION":
      return { ...state, activeId: action.sessionId };
    case "START_ENTRY":
      return {
        ...state,
        activeId: action.sessionId,
        sessions: state.sessions.map((session) =>
          session.id === action.sessionId
            ? {
                ...session,
                title: session.entries.length ? session.title : action.entry.question.slice(0, 68),
                updatedAt: Date.now(),
                entries: [...session.entries, action.entry],
              }
            : session,
        ),
      };
    case "AGENT_COMPLETED":
      return updateEntry(state, action.entryId, (entry) => {
        const completed = markStep(entry, action.agent);
        const nextAgent =
          action.agent === "analyze_situation"
            ? "retrieve_graph_evidence"
            : action.agent === "synthesize_answer"
              ? "critique_answer"
              : null;
        if (!nextAgent || completed.steps.some((step) => step.agent === nextAgent)) {
          return completed;
        }
        return {
          ...completed,
          steps: [
            ...completed.steps,
            { agent: nextAgent, label: AGENT_LABELS[nextAgent], status: "active" },
          ],
        };
      });
    case "RETRIEVAL_COMPLETED":
      return updateEntry(state, action.entryId, (entry) => {
        const retrievalCount = entry.retrievalCount + 1;
        const label =
          retrievalCount > 1
            ? "Truy xuất bổ sung"
            : "Truy xuất căn cứ";
        return { ...markStep(entry, "retrieve_graph_evidence", label), retrievalCount };
      });
    case "ADD_CITATION":
      return updateEntry(state, action.entryId, (entry) => ({
        ...entry,
        citations: entry.citations.some(
          (citation) => citation.citation_id === action.citation.citation_id,
        )
          ? entry.citations
          : [...entry.citations, action.citation],
      }));
    case "ADD_DELTA":
      return updateEntry(state, action.entryId, (entry) => ({
        ...entry,
        answer: entry.answer + action.text,
      }));
    case "COMPLETE":
      return updateEntry(state, action.entryId, (entry) => ({
        ...entry,
        completion: action.completion,
        status: "done",
        steps: entry.steps.map((step) => ({ ...step, status: "done" })),
      }));
    case "FAIL":
      return updateEntry(state, action.entryId, (entry) => ({
        ...entry,
        status: "error",
        error: action.error,
        steps: entry.steps.map((step) =>
          step.status === "active" ? { ...step, status: "done" } : step,
        ),
      }));
  }
}

export function createSession(id: string): ChatSession {
  return { id, title: "Hồ sơ nghiên cứu mới", updatedAt: Date.now(), entries: [] };
}

export function createEntry(id: string, question: string): ChatEntry {
  return {
    id,
    question,
    answer: "",
    citations: [],
    steps: [
      {
        agent: "analyze_situation",
        label: AGENT_LABELS.analyze_situation,
        status: "active",
      },
    ],
    completion: null,
    status: "streaming",
    retrievalCount: 0,
  };
}
