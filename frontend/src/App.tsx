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
  Command,
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
import { useState } from "react";

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

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark"><ShieldCheck size={21} /></span>
        <strong>EvidenceGraph</strong>
      </div>
      <nav aria-label="Primary navigation">
        {nav.map(([Icon, label]) => (
          <button className={label === "Cases" ? "nav-item active" : "nav-item"} key={label} type="button">
            <Icon size={17} /><span>{label}</span>
            {label === "Cases" ? <small>12</small> : null}
            {label === "Alerts" ? <small className="danger">4</small> : null}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <button className="nav-item" type="button"><BookOpen size={17} /> Knowledge base</button>
        <button className="nav-item" type="button"><Settings size={17} /> Settings</button>
        <div className="system-health"><span /> System healthy <ChevronRight size={13} /></div>
        <div className="user">
          <CircleUserRound size={30} />
          <div><strong>Daniel Kim</strong><small>Senior Investigator</small></div>
        </div>
      </div>
    </aside>
  );
}

function Topbar() {
  return (
    <header className="topbar">
      <div className="breadcrumb"><span>Cases</span><b>/</b><strong>EG-2026-0147</strong></div>
      <button className="search" type="button">
        <Search size={16} /><span>Search cases, entities, evidence…</span><kbd>⌘ K</kbd>
      </button>
      <div className="top-actions">
        <span className="sync"><i /> Synced 2 min ago</span>
        <button className="icon-button" aria-label="Notifications" type="button"><Bell size={17} /></button>
        <button className="run-button" type="button"><Play fill="currentColor" size={14} /> Run investigation</button>
      </div>
    </header>
  );
}

function CaseHeader() {
  return (
    <section className="case-header">
      <div className="case-copy">
        <div className="title-row">
          <FolderKanban size={28} />
          <h1>Project Meridian</h1>
          <span className="risk-label">High risk</span>
          <span className="status-label"><CheckCircle2 size={13} /> Active</span>
          <span className="tag">AML</span><span className="tag">Sanctions</span>
        </div>
        <p>Cross-border layering network involving trade-based laundering and crypto off-ramps.</p>
        <div className="case-stats"><span>42 entities</span><i /><span>118 relationships</span><i /><span>29 verified evidence items</span></div>
      </div>
      <div className="case-meta">
        <div className="risk-score"><span>Risk score</span><strong>87<small>/100</small></strong></div>
        <div><span>Assigned investigators</span><div className="avatars"><i>DK</i><i>SK</i><i>AM</i><i>+2</i></div></div>
        <div><span>Last updated</span><strong>May 19, 2026 · 14:32 UTC</strong><small>by Sarah Chen</small></div>
        <div className="policy"><ShieldCheck size={15} /> Policy enforced<small>Immutable audit log</small></div>
      </div>
    </section>
  );
}

function Copilot() {
  return (
    <aside className="copilot panel" aria-label="Investigation Copilot">
      <div className="copilot-title"><Sparkles size={17} /><h2>Investigation Copilot</h2></div>
      <span className="review-chip">AI suggestion — requires review</span>
      <h3>Three transfers form a 72-hour circular flow.</h3>
      <p>Funds move from Nova Meridian Ltd through Orion Trade GmbH to Wallet 0x7A…91F within 72 hours.</p>
      <div className="citations"><span>Cited evidence</span><button type="button">E-018</button><button type="button">E-021</button><button type="button">E-024</button></div>
      <div className="copilot-actions"><button type="button">Inspect path</button><button type="button">Draft hypothesis</button></div>
    </aside>
  );
}

export function App() {
  const [selectedEdgeId, setSelectedEdgeId] = useState("e3");

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="workspace">
        <Topbar />
        <main>
          <CaseHeader />
          <div className="investigation-grid">
            <GraphCanvas selectedEdgeId={selectedEdgeId} onSelectEdge={setSelectedEdgeId} />
            <EvidenceInspector />
            <Timeline />
            <Copilot />
          </div>
        </main>
      </div>
      <div className="command-hint" aria-hidden="true"><Command size={13} /> Evidence-first workspace</div>
    </div>
  );
}
