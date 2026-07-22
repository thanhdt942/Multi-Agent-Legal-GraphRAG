"use client";

import { ArrowRight, Gavel, GitDiff, UserFocus } from "@phosphor-icons/react";

const prompts = [
  {
    icon: Gavel,
    label: "HÀNH VI BỊ CẤM",
    title: "Lấn, chiếm đất được quy định thế nào?",
    question: "Luật Đất đai 2024 quy định thế nào về hành vi lấn chiếm đất?",
  },
  {
    icon: GitDiff,
    label: "ĐỐI CHIẾU LỊCH SỬ",
    title: "Điểm thay đổi giữa Luật 2024 và 2013",
    question: "Quy định về lấn chiếm đất trong Luật Đất đai 2024 thay đổi gì so với Luật Đất đai 2013?",
  },
  {
    icon: UserFocus,
    label: "QUYỀN & NGHĨA VỤ",
    title: "Nghĩa vụ chung của người sử dụng đất",
    question: "Người sử dụng đất có những quyền và nghĩa vụ chung nào theo Luật Đất đai 2024?",
  },
];

export function ResearchEmpty({ onPrompt }: { onPrompt: (question: string) => void }) {
  return (
    <div className="research-empty">
      <div className="brief-number">RESEARCH BRIEF · 01</div>
      <div className="empty-rule" />
      <h1>Phân tích pháp lý,<br /><em>có căn cứ để kiểm tra.</em></h1>
      <p>Đặt tình huống hoặc câu hỏi pháp lý. Mạng lưới tác tử sẽ phân tích, truy xuất đồ thị, đối chiếu lịch sử luật và phản biện từng kết luận trước khi trả lời.</p>
      <div className="prompt-ledger">
        {prompts.map(({ icon: Icon, label, title, question }, index) => (
          <button key={label} type="button" onClick={() => onPrompt(question)}>
            <span className="prompt-number">0{index + 1}</span>
            <Icon size={20} weight="duotone" />
            <span><small>{label}</small><strong>{title}</strong></span>
            <ArrowRight size={18} />
          </button>
        ))}
      </div>
    </div>
  );
}
