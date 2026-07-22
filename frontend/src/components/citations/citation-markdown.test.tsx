import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CitationMarkdown } from "@/components/citations/citation-markdown";

describe("CitationMarkdown", () => {
  it("renders citation markers as accessible buttons", async () => {
    const onCitation = vi.fn();
    render(
      <CitationMarkdown
        text="Lấn đất bị nghiêm cấm [cit_01]."
        streaming={false}
        onCitation={onCitation}
      />,
    );

    const citation = screen.getByRole("button", { name: "Mở trích dẫn cit_01" });
    await userEvent.click(citation);
    expect(onCitation).toHaveBeenCalledWith("cit_01");
  });

  it("does not interpret HTML from model output", () => {
    const { container } = render(
      <CitationMarkdown
        text={'<img src=x onerror="alert(1)"> [cit_02]'}
        streaming={false}
        onCitation={() => undefined}
      />,
    );
    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toContain("<img");
  });
});
