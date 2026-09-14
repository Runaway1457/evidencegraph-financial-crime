import {
  Activity,
  Bell,
  BookOpen,
  Bot,
  Boxes,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  CircleUserRound,
  FileSearch,
  FolderKanban,
  LayoutDashboard,
  Play,
  Scale,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";

import { CaseQueue } from "./CaseQueue";
import { CommandPalette } from "./CommandPalette";
import { edges } from "./demo";
import { EvidenceInspector } from "./EvidenceInspector";
import { GraphCanvas } from "./GraphCanvas";
import { Timeline } from "./Timeline";

const nav = [
  [LayoutDashboard, "Command center"],
  [FolderKanban, "Cases"],
  [Boxes, "Entity graph"],
  [FileSearch, "Evidence ledger"],
  [Activity, "Alerts"],
  [Bot, "AI runs"],
  [Scale, "Reviews"],
  [BriefcaseBusiness, "Reports"],
] as const;

const caseNames: Record<string, string> = {
  "EG-2026-0147": "Project Meridian",
  "EG-2026-0139": "Northstar",
  "EG-2026-0128": "Amber Route",
};

type RunStatus = "ready" | "queued";

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark"><ShieldCheck size={19} /></span>
        <div><strong>EvidenceGraph</strong><small>Financial Crime OS</small></div>
      </div>
      <nav aria-label="Primary navigation">
        <span className="nav-section">Investigate</span>
        {nav.slice(0, 6).map(([Icon, label]) => (
          <button
            aria-current={label === "Cases" ? "page" : undefined}
            className={label === "Cases" ? "nav-item active" : "nav-item"}
            key={label}
            type="button"
          >
            <Icon size={17} /><span>{label}</span>
            {label === "Cases" ? <small>12</small> : null}
            {label === "Alerts" ? <small className="danger">4</small> : null}
          </button>
        ))}
        <span className="nav-section governance">Governance</span>
        {nav.slice(6).map(([Icon, label]) => (
          <button className="nav-item" key={label} type="button">
            <Icon size={17} /><span>{label}</span>
            {label === "Reviews" ? <small>4</small> : null}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <button className="nav-item" type="button"><BookOpen size={17} /><span>Knowledge base</span></button>
        <button className="nav-item" type="button"><Settings size={17} /><span>Settings</span></button>
        <div className="system-health"><span /> All controls enforced <ChevronRight size={13} /></div>
        <div className="user">
          <CircleUserRound size={30} />
          <div><strong>Daniel Kim</strong><small>Senior Investigator</small></div>
          <ChevronRight size={13} />
        </div>
      </div>
    </aside>
  );
}

function Topbar({
  caseId,
  onOpenCommand,
  onRun,
  runStatus,
}: {
  caseId: string;
  onOpenCommand: () => void;
  onRun: () => void;
  runStatus: RunStatus;
}) {
  return (
    <header className="topbar">
      <div className="breadcrumb"><span>Cases</span><b>/</b><strong>{caseId}</strong></div>
      <button className="search" onClick={onOpenCommand} type="button">
        <Search size={16} /><span>Search cases, entities, evidence…</span><kbd>⌘ K</kbd>
      </button>
      <div className="top-actions">
        <span className="sync"><i /> Ledger synced</span>
        <button className="icon-button" aria-label="Notifications" type="button"><Bell size={17} /></button>
        <button
          className={runStatus === "queued" ? "run-button queued" : "run-button"}
          disabled={runStatus === "queued"}
          onClick={onRun}
          type="button"
        >
          {runStatus === "queued" ? <Activity size={14} /> : <Play fill="currentColor" size={13} />}
          {runStatus === "queued" ? "Investigation queued" : "Run investigation"}
        </button>
      </div>
    </header>
  );
}

function CaseHeader({ caseId }: { caseId: string }) {
  return (
    <section className="case-header">
      <div className="case-copy">
        <div className="eyebrow"><span>ACTIVE INVESTIGATION</span><code>{caseId}</code></div>
        <div className="title-row">
          <FolderKanban size={27} />
          <h1>{caseNames[caseId] ?? "Investigation"}</h1>
          <span className="risk-label">High risk</span>
          <span className="status-label"><CheckCircle2 size={12} /> Active</span>
          <span className="tag">AML</span><span className="tag">Sanctions</span>
        </div>
        <p>Cross-border layering network involving trade-based laundering and crypto off-ramps.</p>
        <div className="case-stats">
          <span><strong>42</strong> entities</span><i />
          <span><strong>118</strong> relationships</span><i />
          <span><strong>29</strong> verified evidence items</span>
        </div>
      </div>
      <div className="case-meta">
        <div className="risk-score">
          <span>Composite risk</span>
          <strong>87<small>/100</small></strong>
          <em>+12 this week</em>
        </div>
        <div>
          <span>Investigation team</span>
          <div className="avatars"><i>DK</i><i>SC</i><i>AM</i><i>+2</i></div>
          <small>5 members · 3 online</small>
        </div>
        <div>
          <span>Last material event</span>
          <strong>May 19 · 14:32 UTC</strong>
          <small>Human verification by Sarah Chen</small>
        </div>
        <div className="policy">
          <ShieldCheck size={15} />
          <span>OPA policy enforced</span>
          <small>Immutable audit log · PII shielded</small>
        </div>
      </div>
    </section>
  );
}

function Copilot() {
  return (
    <aside className="copilot panel" aria-label="Investigation Copilot">
      <div className="copilot-title">
        <div><Sparkles size={16} /><h2>Investigation Copilot</h2></div>
        <code>AIR-019</code>
      </div>
      <span className="review-chip">AI hypothesis · unverified</span>
      <h3>Three transfers form a 72-hour circular flow.</h3>
      <p>
        Funds move through a trade counterparty to a crypto off-ramp. The conclusion is
        grounded in three verified records and remains non-authoritative until review.
      </p>
      <div className="reasoning-path">
        <span>Nova Meridian</span><i>→</i><span>Orion Trade</span><i>→</i><span>0x7A…91F</span>
      </div>
      <div className="citations">
        <span>Cited evidence</span><button type="button">E-018</button>
        <button type="button">E-021</button><button type="button">E-027</button>
      </div>
      <div className="guardrail">
        <ShieldCheck size={14} />
        <span><strong>Write blocked</strong> · reviewer approval required</span>
      </div>
      <div className="copilot-actions">
        <button type="button">Inspect path</button><button type="button">Draft hypothesis</button>
      </div>
    </aside>
  );
}

export function App() {
  const [selectedEdgeId, setSelectedEdgeId] = useState("e3");
  const [activeCaseId, setActiveCaseId] = useState("EG-2026-0147");
  const [commandOpen, setCommandOpen] = useState(false);
  const [runStatus, setRunStatus] = useState<RunStatus>("ready");
  const selectedEdge = edges.find((edge) => edge.id === selectedEdgeId);

  if (!selectedEdge) throw new Error(`Unknown selected relationship: ${selectedEdgeId}`);

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((current) => !current);
      }
      if (event.key === "Escape") setCommandOpen(false);
    };

    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="workspace">
        <Topbar
          caseId={activeCaseId}
          onOpenCommand={() => setCommandOpen(true)}
          onRun={() => setRunStatus("queued")}
          runStatus={runStatus}
        />
        <main>
          <CaseHeader caseId={activeCaseId} />
          <div className="investigation-grid">
            <CaseQueue activeCaseId={activeCaseId} onSelectCase={setActiveCaseId} />
            <GraphCanvas selectedEdgeId={selectedEdgeId} onSelectEdge={setSelectedEdgeId} />
            <EvidenceInspector edge={selectedEdge} />
            <Timeline />
            <Copilot />
          </div>
        </main>
      </div>
      <CommandPalette open={commandOpen} onClose={() => setCommandOpen(false)} />
      <div className="security-ribbon" aria-hidden="true">
        <ShieldCheck size={12} /> EVIDENCE-FIRST · ZERO DIRECT AI WRITES
      </div>
    </div>
  );
}
