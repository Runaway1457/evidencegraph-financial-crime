import {
  BadgeCheck,
  DatabaseZap,
  ExternalLink,
  FileCheck2,
  Fingerprint,
  GitBranch,
  LockKeyhole,
  MoreHorizontal,
  ScanText,
} from "lucide-react";
import { useState } from "react";

import { evidence, nodes } from "./demo";
import type { GraphEdge } from "./types";

interface EvidenceInspectorProps {
  edge: GraphEdge;
}

function entityLabel(id: string): string {
  return nodes.find((node) => node.id === id)?.label ?? "Unknown entity";
}

export function EvidenceInspector({ edge }: EvidenceInspectorProps) {
  const supporting = evidence.filter((item) => edge.evidenceIds.includes(item.id));
  const [selectedEvidenceId, setSelectedEvidenceId] = useState(edge.evidenceIds[0] ?? "");
  const selectedEvidence =
    supporting.find((item) => item.id === selectedEvidenceId) ?? supporting[0];

  return (
    <aside className="inspector panel" aria-label="Relationship evidence inspector">
      <div className="inspector-titlebar">
        <span>Relationship intelligence</span>
        <button className="icon-button" aria-label="More relationship actions" type="button">
          <MoreHorizontal size={16} />
        </button>
      </div>
      <div className="inspector-heading">
        <span className="relationship-glyph"><GitBranch size={18} /></span>
        <div>
          <small>Selected relation · {edge.id.toUpperCase()}</small>
          <h2>{edge.label}</h2>
        </div>
      </div>
      <div className="badges">
        <span className="badge verified"><BadgeCheck size={13} /> Evidence-backed</span>
        <span className="badge confidence">Confidence {edge.confidence}%</span>
        {edge.suspicious ? <span className="badge elevated">Elevated</span> : null}
      </div>
      <dl className="relationship-grid">
        <div><dt>From</dt><dd>{entityLabel(edge.source)}</dd></div>
        <div><dt>To</dt><dd>{entityLabel(edge.target)}</dd></div>
        <div><dt>Observed value</dt><dd>{edge.label}</dd></div>
        <div><dt>Event time</dt><dd>{edge.detail ?? "Registry event"}</dd></div>
      </dl>
      <div className="why">
        <div className="section-kicker"><ScanText size={13} /><h3>Analytic rationale</h3></div>
        <p>{edge.rationale}</p>
      </div>
      <div className="evidence-heading">
        <div className="section-kicker"><DatabaseZap size={13} /><h3>Supporting evidence</h3></div>
        <span>{supporting.length}</span>
      </div>
      <div className="evidence-list">
        {supporting.map((item) => (
          <button
            aria-pressed={selectedEvidence?.id === item.id}
            className={selectedEvidence?.id === item.id ? "evidence-row selected" : "evidence-row"}
            key={item.id}
            onClick={() => setSelectedEvidenceId(item.id)}
            type="button"
          >
            <span className="evidence-icon"><FileCheck2 size={17} /></span>
            <span className="evidence-copy">
              <strong>{item.title}</strong>
              <small>{item.source} · {item.date}</small>
              <small className="hash">sha256:{item.hash}</small>
            </span>
            <span className="evidence-id">{item.id}</span>
          </button>
        ))}
      </div>
      {selectedEvidence ? (
        <div className="locator-card" aria-label="Selected evidence provenance">
          <div><Fingerprint size={14} /><span>Source locator</span><strong>Verified</strong></div>
          <code>{selectedEvidence.locator}</code>
          <small><LockKeyhole size={12} /> Attested by {selectedEvidence.verifiedBy}</small>
        </div>
      ) : null}
      <button className="evidence-chain" type="button">
        <GitBranch size={15} />
        <span>Inspect custody chain</span>
        <code>HEAD 9fd3…81ac</code>
      </button>
      <div className="inspector-actions">
        <button className="secondary" type="button"><ExternalLink size={15} /> Open source</button>
        <button className="primary" type="button"><FileCheck2 size={15} /> Propose finding</button>
      </div>
    </aside>
  );
}
