"use client";

import {
  Archive,
  Books,
  FilePlus,
  Graph,
  Scales,
} from "@phosphor-icons/react";

import type { ChatSession } from "@/lib/answer-types";

interface ResearchNavigatorProps {
  sessions: ChatSession[];
  activeId: string;
  health: "checking" | "online" | "offline";
  onNew: () => void;
  onSelect: (sessionId: string) => void;
}

export function ResearchNavigator({
  sessions,
  activeId,
  health,
  onNew,
  onSelect,
}: ResearchNavigatorProps) {
  return (
    <div className="navigator-content">
      <div className="brand-lockup">
        <span className="brand-glyph"><Scales size={22} weight="duotone" /></span>
        <span><strong>PHÁP ĐIỂN</strong><small>LEGAL RESEARCH OS</small></span>
      </div>

      <button className="new-dossier" type="button" onClick={onNew}>
        <FilePlus size={18} />
        Hồ sơ nghiên cứu mới
      </button>

      <section className="navigator-section" aria-labelledby="recent-heading">
        <div className="navigator-heading" id="recent-heading">
          <span>Hồ sơ gần đây</span><Archive size={15} />
        </div>
        <div className="session-list">
          {sessions.length ? (
            sessions.map((session) => (
              <button
                key={session.id}
                className={`session-item ${session.id === activeId ? "session-active" : ""}`}
                type="button"
                onClick={() => onSelect(session.id)}
              >
                <span className="session-index">{String(session.entries.length).padStart(2, "0")}</span>
                <span><strong>{session.title}</strong><small>{session.entries.length} lượt nghiên cứu</small></span>
              </button>
            ))
          ) : (
            <p className="empty-history">Chưa có hồ sơ nào được lưu.</p>
          )}
        </div>
      </section>

      <section className="corpus-card" aria-label="Phạm vi kho luật">
        <div className="corpus-icon"><Books size={19} /></div>
        <div><span>KHO LUẬT ĐANG DÙNG</span><strong>Đất đai 2013 — 2024</strong></div>
        <div className={`backend-status status-${health}`}>
          <i /> {health === "online" ? "Graph trực tuyến" : health === "offline" ? "Mất kết nối" : "Đang kiểm tra"}
        </div>
      </section>

      <div className="navigator-footer"><Graph size={16} /> Neo4j · LangGraph · OpenAI</div>
    </div>
  );
}
