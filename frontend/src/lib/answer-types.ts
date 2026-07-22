export type AgentName =
  | "analyze_situation"
  | "retrieve_graph_evidence"
  | "compare_historical_law"
  | "synthesize_answer"
  | "critique_answer";

export type Confidence = "HIGH" | "MEDIUM" | "LOW";
export type ClaimSupport = "DIRECT" | "INFERRED" | "UNSUPPORTED";

export interface Citation {
  citation_id: string;
  node_id: string;
  document_id?: string | null;
  document_number?: string | null;
  document_name?: string | null;
  chapter?: string | null;
  section?: string | null;
  article?: string | null;
  clause?: string | null;
  point?: string | null;
  display?: string;
  quote?: string;
  source_url?: string | null;
  validity_status?: string | null;
  retrieved_at?: string | null;
}

export interface LegalClaim {
  text: string;
  citation_ids: string[];
  support: ClaimSupport;
}

export interface Usage {
  input_tokens: number;
  output_tokens: number;
}

export interface AnswerCompletion {
  answer_id: string;
  thread_id: string;
  confidence: Confidence;
  abstained: boolean;
  claims: LegalClaim[];
  warnings: string[];
  usage: Usage;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AnswerRequest {
  question: string;
  thread_id: string;
  messages: ConversationMessage[];
  retrieval: {
    strategy: "auto";
    filters: {
      document_ids: string[];
      levels: Array<"article" | "clause" | "point">;
      validity_statuses: string[];
    };
    top_k: number;
    relationship_statuses: Array<"VERIFIED">;
    context_token_budget: number;
  };
  generation: {
    language: "vi";
    format: "markdown";
    temperature: number;
    max_output_tokens: number;
    require_citations: boolean;
    abstain_when_insufficient: boolean;
  };
  include_retrieval: false;
}

export type SseEvent =
  | { event: "agent.completed"; data: { agent: AgentName } }
  | {
      event: "retrieval.completed";
      data: { retrieval_id: string | null; citation_count: number };
    }
  | { event: "citation"; data: { citation_id: string; citation: Citation } }
  | { event: "answer.delta"; data: { text: string } }
  | { event: "answer.completed"; data: AnswerCompletion }
  | { event: "error"; data: { code: string; message: string; retryable: boolean } };

export interface AgentStep {
  agent: AgentName;
  label: string;
  status: "active" | "done";
}

export interface ChatEntry {
  id: string;
  question: string;
  answer: string;
  citations: Citation[];
  steps: AgentStep[];
  completion: AnswerCompletion | null;
  status: "streaming" | "done" | "error";
  error?: string;
  retrievalCount: number;
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: number;
  entries: ChatEntry[];
}
