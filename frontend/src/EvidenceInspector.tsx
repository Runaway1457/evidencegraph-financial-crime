import {
  BadgeCheck,
  ExternalLink,
  FileCheck2,
  GitBranch,
  MoreHorizontal,
} from "lucide-react";

import { evidence } from "./demo";

export function EvidenceInspector() {
  return (
    <aside className="inspector panel" aria-label="Relationship evidence inspector">
      <div className="inspector-titlebar">
        <span>Relationship details</span>
        <button className="icon-button" aria-label="More relationship actions" type="button">
          <MoreHorizontal size={16} />
        </button>
      </div>
      <div className="inspector-heading">
        <GitBranch size={19} />
        <h2>Circular transfer pattern</h2>
      </div>
      <div className="badges">
        <span className="badge verified"><BadgeCheck size={13} /> Evidence-backed</span>
        <span className="badge confidence">Confidence 94%</span>
      </div>
      <dl className="relationship-grid">
        <div><dt>From</dt><dd>Nova Meridian Ltd</dd></div>
        <div><dt>To</dt><dd>Orion Trade GmbH</dd></div>
        <div><dt>Amount</dt><dd>USD 2.38M</dd></div>
        <div><dt>Date</dt><dd>May 14, 2026</dd></div>
      </dl>
      <div className="why">
        <h3>Why this matters</h3>
        <p>
          Forms the middle leg of a 72-hour circular flow moving funds through
          a trade counterparty before conversion to a crypto wallet.
        </p>
      </div>
      <div className="evidence-heading">
        <h3>Supporting evidence</h3>
        <span>{evidence.length}</span>
      </div>
      <div className="evidence-list">
        {evidence.map((item) => (
          <button className="evidence-row" key={item.id} type="button">
            <span className="evidence-icon"><FileCheck2 size={17} /></span>
            <span className="evidence-copy">
              <strong>{item.title}</strong>
              <small>{item.source} · {item.date}</small>
              <small className="hash">sha256:{item.hash} · {item.locator}</small>
            </span>
            <span className="evidence-id">{item.id}</span>
          </button>
        ))}
      </div>
      <button className="evidence-chain" type="button">
        <GitBranch size={15} /> Inspect immutable evidence chain
      </button>
      <div className="inspector-actions">
        <button className="secondary" type="button"><ExternalLink size={15} /> Open source</button>
        <button className="primary" type="button"><FileCheck2 size={15} /> Propose finding</button>
      </div>
    </aside>
  );
}
