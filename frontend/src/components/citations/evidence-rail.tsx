"use client";

import { ArrowSquareOut, FileText, MagnifyingGlass, Quotes } from "@phosphor-icons/react";
import { useDeferredValue, useEffect, useId, useState } from "react";

import type { Citation } from "@/lib/answer-types";

interface EvidenceRailProps {
  citations: Citation[];
  selectedId: string | null;
  onSelect: (citationId: string) => void;
}

function locationLabel(citation: Citation): string {
  return [
    citation.point && `Điểm ${citation.point}`,
    citation.clause && `Khoản ${citation.clause}`,
    citation.article && `Điều ${citation.article}`,
  ].filter(Boolean).join(" · ") || citation.display || "Nội dung nguồn";
}

function safeUrl(value?: string | null): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

export function EvidenceRail({ citations, selectedId, onSelect }: EvidenceRailProps) {
  const [query, setQuery] = useState("");
  const searchId = useId();
  const deferredQuery = useDeferredValue(query.toLocaleLowerCase("vi"));
  const selected = citations.find((citation) => citation.citation_id === selectedId) ?? citations[0];
  const filtered = citations.filter((citation) =>
    `${citation.document_name ?? ""} ${locationLabel(citation)} ${citation.quote ?? ""}`
      .toLocaleLowerCase("vi")
      .includes(deferredQuery),
  );

  useEffect(() => {
    if (selectedId) {
      document.querySelector(`[data-evidence-id="${CSS.escape(selectedId)}"]`)?.scrollIntoView({
        block: "nearest",
      });
    }
  }, [selectedId]);

  return (
    <div className="evidence-content">
      <header className="evidence-header">
        <div><span className="section-kicker">EVIDENCE DESK</span><h2>Nguồn viện dẫn <b>{citations.length}</b></h2></div>
        <div className="evidence-search">
          <MagnifyingGlass size={16} aria-hidden="true" />
          <label className="sr-only" htmlFor={searchId}>Tìm trong nguồn viện dẫn</label>
          <input
            id={searchId}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Tìm Điều, Khoản..."
          />
        </div>
      </header>

      {selected ? (
        <article className="selected-evidence">
          <div className="selected-evidence-top">
            <span className="source-chip">{selected.citation_id.toUpperCase()}</span>
            <span className="validity-chip">{selected.validity_status || "Nguồn dữ liệu"}</span>
          </div>
          <h3>{selected.document_name || "Văn bản pháp luật"}</h3>
          <p className="source-locator">{locationLabel(selected)}</p>
          <blockquote><Quotes size={18} weight="fill" aria-hidden="true" />{selected.quote || "Không có nội dung trích dẫn."}</blockquote>
          {safeUrl(selected.source_url) && (
            <a href={safeUrl(selected.source_url) ?? undefined} target="_blank" rel="noopener noreferrer">
              Mở văn bản gốc <ArrowSquareOut size={15} />
            </a>
          )}
        </article>
      ) : (
        <div className="evidence-empty">
          <FileText size={34} weight="thin" />
          <strong>Chưa có nguồn viện dẫn</strong>
          <p>Mỗi trích dẫn được gửi trước nội dung trả lời và sẽ xuất hiện tại đây.</p>
        </div>
      )}

      {citations.length > 0 && (
        <div className="evidence-index" aria-label="Danh mục nguồn viện dẫn">
          <div className="evidence-index-label">DANH MỤC · {filtered.length}</div>
          {filtered.map((citation) => (
            <button
              key={citation.citation_id}
              type="button"
              data-evidence-id={citation.citation_id}
              className={`evidence-row ${citation.citation_id === selected?.citation_id ? "evidence-row-active" : ""}`}
              onClick={() => onSelect(citation.citation_id)}
            >
              <span>{citation.citation_id.replace("cit_", "")}</span>
              <span><strong>{locationLabel(citation)}</strong><small>{citation.document_name || "Văn bản pháp luật"}</small></span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
