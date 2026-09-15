import { AlertTriangle, CheckCircle2, Clock3, UserRoundCheck } from "lucide-react";
import type { CaseQueueItem } from "./types";

interface CaseQueueProps {
  activeCaseId: string;
  cases: readonly CaseQueueItem[];
  onSelectCase: (caseId: string) => void;
}

export function CaseQueue({ activeCaseId, cases, onSelectCase }: CaseQueueProps) {
  return (
    <aside className="case-queue panel" aria-label="Priority case queue">
      <div className="queue-heading">
        <div>
          <span>Priority queue</span>
          <strong>{cases.length} active cases</strong>
        </div>
        <button aria-label="Queue options" type="button">•••</button>
      </div>
      <div className="queue-health">
        <span><i /> 3 analysts online</span>
        <span>Median SLA 4.2h</span>
      </div>
      <div className="queue-list">
        {cases.map((item, index) => (
          <button
            aria-current={item.id === activeCaseId ? "page" : undefined}
            className={item.id === activeCaseId ? "case-item active" : "case-item"}
            key={item.id}
            onClick={() => onSelectCase(item.id)}
            type="button"
          >
            <span className="queue-rank">0{index + 1}</span>
            <span className="queue-copy">
              <small>{item.id}</small>
              <strong>{item.name}</strong>
              <span>{item.cue}</span>
            </span>
            <span className="queue-score">
              <strong>{item.risk ?? "—"}</strong>
              <small>{item.age}</small>
            </span>
          </button>
        ))}
      </div>
      <div className="review-stack">
        <div className="review-heading">
          <span><UserRoundCheck size={14} /> Review queue</span>
          <strong>04</strong>
        </div>
        <article>
          <span className="review-icon urgent"><AlertTriangle size={14} /></span>
          <div><strong>Finding F-008</strong><small>Independent review due in 38m</small></div>
        </article>
        <article>
          <span className="review-icon"><Clock3 size={14} /></span>
          <div><strong>Evidence packet</strong><small>Awaiting legal hold approval</small></div>
        </article>
        <article>
          <span className="review-icon complete"><CheckCircle2 size={14} /></span>
          <div><strong>Chain verification</strong><small>29 / 29 objects verified</small></div>
        </article>
      </div>
      <div className="queue-foot">
        <span>Workload</span>
        <div><i style={{ width: "72%" }} /></div>
        <strong>72%</strong>
      </div>
    </aside>
  );
}
