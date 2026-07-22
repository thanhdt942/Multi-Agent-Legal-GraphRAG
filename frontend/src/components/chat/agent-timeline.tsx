import { Check, CircleNotch } from "@phosphor-icons/react";

import type { AgentStep } from "@/lib/answer-types";

export function AgentTimeline({ steps }: { steps: AgentStep[] }) {
  return (
    <ol className="agent-timeline" aria-label="Tiến trình tác tử">
      {steps.map((step, index) => (
        <li className={`agent-node agent-${step.status}`} key={`${step.agent}-${index}`}>
          <span className="agent-node-icon" aria-hidden="true">
            {step.status === "done" ? <Check size={12} weight="bold" /> : <CircleNotch size={13} />}
          </span>
          <span>{step.label}</span>
        </li>
      ))}
    </ol>
  );
}
