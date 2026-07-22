"use client";

import {
  FileText,
  List,
  SealCheck,
} from "@phosphor-icons/react";
import clsx from "clsx";
import { startTransition, useEffect, useReducer, useRef, useState } from "react";

import { AssistantAnswer } from "@/components/chat/assistant-answer";
import { MessageComposer } from "@/components/chat/message-composer";
import { EvidenceRail } from "@/components/citations/evidence-rail";
import { ResearchNavigator } from "@/components/history/research-navigator";
import { Sheet } from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { ResearchEmpty } from "@/components/workbench/research-empty";
import { useAnswerStream } from "@/hooks/use-answer-stream";
import type { AnswerRequest, ChatEntry, ChatSession, SseEvent } from "@/lib/answer-types";
import {
  chatReducer,
  createEntry,
  createSession,
  initialChatState,
} from "@/lib/chat-reducer";
import { loadSessions, saveSessions } from "@/lib/storage";

function id(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

function lastEntry(session: ChatSession | undefined): ChatEntry | undefined {
  return session?.entries.at(-1);
}

function answerPayload(session: ChatSession, question: string, compare: boolean): AnswerRequest {
  return {
    question,
    thread_id: session.id,
    messages: session.entries
      .filter((entry) => entry.status === "done")
      .slice(-3)
      .flatMap((entry) => [
        { role: "user" as const, content: entry.question },
        { role: "assistant" as const, content: entry.answer },
      ]),
    retrieval: {
      strategy: "auto",
      filters: {
        document_ids: compare ? ["177815", "32833"] : ["177815"],
        levels: ["article", "clause", "point"],
        validity_statuses: compare ? [] : ["Còn hiệu lực", "Hết hiệu lực một phần"],
      },
      top_k: 8,
      relationship_statuses: ["VERIFIED"],
      context_token_budget: 7000,
    },
    generation: {
      language: "vi",
      format: "markdown",
      temperature: 0.1,
      max_output_tokens: 800,
      require_citations: true,
      abstain_when_insufficient: true,
    },
    include_retrieval: false,
  };
}

export function LegalWorkbench() {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);
  const [health, setHealth] = useState<"checking" | "online" | "offline">("checking");
  const [navigatorOpen, setNavigatorOpen] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null);
  const [selectedCitationId, setSelectedCitationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const stream = useAnswerStream();

  const activeSession = state.sessions.find((session) => session.id === state.activeId);
  const selectedEntry =
    activeSession?.entries.find((entry) => entry.id === selectedEntryId) ?? lastEntry(activeSession);
  const latestAnswerLength = lastEntry(activeSession)?.answer.length ?? 0;

  useEffect(() => {
    const stored = loadSessions();
    const sessions = stored.length ? stored : [createSession(id("thread"))];
    dispatch({ type: "HYDRATE", sessions, activeId: sessions[0].id });
  }, []);

  useEffect(() => {
    if (!state.hydrated) return;
    const timeout = window.setTimeout(() => saveSessions(state.sessions), 300);
    return () => window.clearTimeout(timeout);
  }, [state.hydrated, state.sessions]);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then((response) => setHealth(response.ok ? "online" : "offline"))
      .catch(() => setHealth("offline"));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [latestAnswerLength, activeSession?.entries.length]);

  function newSession() {
    if (stream.streaming) return;
    const session = createSession(id("thread"));
    dispatch({ type: "NEW_SESSION", session });
    setSelectedEntryId(null);
    setSelectedCitationId(null);
    setNavigatorOpen(false);
  }

  function selectSession(sessionId: string) {
    if (stream.streaming) return;
    const session = state.sessions.find((item) => item.id === sessionId);
    startTransition(() => dispatch({ type: "SELECT_SESSION", sessionId }));
    setSelectedEntryId(lastEntry(session)?.id ?? null);
    setSelectedCitationId(lastEntry(session)?.citations[0]?.citation_id ?? null);
    setNavigatorOpen(false);
  }

  function selectCitation(entryId: string, citationId: string) {
    setSelectedEntryId(entryId);
    setSelectedCitationId(citationId);
    if (window.innerWidth < 1240) setEvidenceOpen(true);
  }

  async function submit(question: string, compare: boolean) {
    if (!activeSession || stream.streaming) return;
    const entry = createEntry(id("entry"), question);
    dispatch({ type: "START_ENTRY", sessionId: activeSession.id, entry });
    setSelectedEntryId(entry.id);
    setSelectedCitationId(null);
    let completed = false;

    function handleEvent(event: SseEvent) {
      switch (event.event) {
        case "agent.completed":
          dispatch({ type: "AGENT_COMPLETED", entryId: entry.id, agent: event.data.agent });
          break;
        case "retrieval.completed":
          dispatch({
            type: "RETRIEVAL_COMPLETED",
            entryId: entry.id,
            citationCount: event.data.citation_count,
          });
          break;
        case "citation":
          dispatch({ type: "ADD_CITATION", entryId: entry.id, citation: event.data.citation });
          setSelectedCitationId((current) => current ?? event.data.citation.citation_id);
          break;
        case "answer.delta":
          dispatch({ type: "ADD_DELTA", entryId: entry.id, text: event.data.text });
          break;
        case "answer.completed":
          completed = true;
          dispatch({ type: "COMPLETE", entryId: entry.id, completion: event.data });
          break;
        case "error":
          throw new Error(event.data.message || "Luồng trả lời bị gián đoạn.");
      }
    }

    try {
      await stream.start(answerPayload(activeSession, question, compare), handleEvent);
      if (!completed) throw new Error("Máy chủ kết thúc luồng trước khi hoàn tất câu trả lời.");
    } catch (error) {
      const message =
        error instanceof DOMException && error.name === "AbortError"
          ? "Yêu cầu đã được dừng theo lựa chọn của bạn."
          : error instanceof Error
            ? error.message
            : "Không thể kết nối tới máy chủ.";
      dispatch({ type: "FAIL", entryId: entry.id, error: message });
    }
  }

  const navigator = (
    <ResearchNavigator
      sessions={state.sessions}
      activeId={state.activeId}
      health={health}
      onNew={newSession}
      onSelect={selectSession}
    />
  );
  const evidence = (
    <EvidenceRail
      citations={selectedEntry?.citations ?? []}
      selectedId={selectedCitationId}
      onSelect={setSelectedCitationId}
    />
  );

  return (
    <main className="workbench-shell">
      <a className="skip-link" href="#research-thread">Chuyển đến nội dung nghiên cứu</a>
      <aside className="desktop-navigator" aria-label="Hồ sơ nghiên cứu">{navigator}</aside>

      <section className="research-column">
        <header className="workbench-header">
          <button className="icon-button mobile-control" type="button" onClick={() => setNavigatorOpen(true)} aria-label="Mở hồ sơ nghiên cứu">
            <List size={20} />
          </button>
          <div className="dossier-heading">
            <span>HỒ SƠ / {String(activeSession?.entries.length ?? 0).padStart(2, "0")}</span>
            <h2>{activeSession?.title ?? "Đang chuẩn bị workbench"}</h2>
          </div>
          <div className="header-actions">
            <span className={clsx("verified-state", health === "online" && "verified-online")}><SealCheck size={16} weight="fill" /> {health === "online" ? "Hệ thống sẵn sàng" : "Đang kiểm tra"}</span>
            <ThemeToggle />
            <button className="icon-button evidence-control" type="button" onClick={() => setEvidenceOpen(true)} aria-label="Mở nguồn viện dẫn">
              <FileText size={19} /><b>{selectedEntry?.citations.length ?? 0}</b>
            </button>
          </div>
        </header>

        <div className="research-thread" id="research-thread" ref={scrollRef} aria-live="polite">
          {!activeSession?.entries.length ? (
            <ResearchEmpty onPrompt={(question) => submit(question, question.includes("2013"))} />
          ) : (
            <div className="thread-ledger">
              {activeSession.entries.map((entry, index) => (
                <section className="research-turn" key={entry.id}>
                  <div className="question-record"><span>Q{String(index + 1).padStart(2, "0")}</span><p>{entry.question}</p></div>
                  <AssistantAnswer
                    entry={entry}
                    onCitation={(citationId) => selectCitation(entry.id, citationId)}
                    onOpenEvidence={() => {
                      setSelectedEntryId(entry.id);
                      setSelectedCitationId(entry.citations[0]?.citation_id ?? null);
                      setEvidenceOpen(true);
                    }}
                  />
                </section>
              ))}
            </div>
          )}
        </div>

        <MessageComposer
          streaming={stream.streaming}
          disabled={!state.hydrated}
          onSubmit={submit}
          onStop={stream.stop}
        />
      </section>

      <aside className="desktop-evidence" aria-label="Nguồn viện dẫn">{evidence}</aside>

      <Sheet open={navigatorOpen} onOpenChange={setNavigatorOpen} title="Hồ sơ nghiên cứu" side="left">
        {navigator}
      </Sheet>
      <Sheet open={evidenceOpen} onOpenChange={setEvidenceOpen} title="Nguồn viện dẫn" side="right">
        {evidence}
      </Sheet>
    </main>
  );
}
