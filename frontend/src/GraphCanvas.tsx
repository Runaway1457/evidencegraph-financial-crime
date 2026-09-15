import {
  Crosshair,
  Eye,
  EyeOff,
  Layers3,
  Maximize2,
  Minus,
  Plus,
  Route,
  ScanSearch,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";

import { edges, nodes } from "./demo";
import type { EntityKind, GraphEdge, GraphNode } from "./types";

const colors: Record<EntityKind, string> = {
  company: "#54c7ff",
  person: "#ad8aff",
  account: "#42d3a2",
  wallet: "#ffb84d",
  jurisdiction: "#ff676f",
  service: "#8b9aaf",
};

interface GraphCanvasProps {
  selectedEdgeId: string;
  onSelectEdge: (edgeId: string) => void;
}

function endpoint(nodeId: string): GraphNode {
  const node = nodes.find((item) => item.id === nodeId);
  if (!node) throw new Error(`Unknown graph node: ${nodeId}`);
  return node;
}

function Edge({
  edge,
  selected,
  provenanceVisible,
  onSelect,
}: {
  edge: GraphEdge;
  selected: boolean;
  provenanceVisible: boolean;
  onSelect: () => void;
}) {
  const source = endpoint(edge.source);
  const target = endpoint(edge.target);
  const midX = (source.x + target.x) / 2;
  const midY = (source.y + target.y) / 2;
  const activate = (event: ReactKeyboardEvent<SVGLineElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect();
    }
  };

  return (
    <g className={edge.suspicious ? "graph-edge suspicious" : "graph-edge"}>
      <line
        aria-label={`${source.label} to ${target.label}: ${edge.label}`}
        className={selected ? "edge-line selected" : "edge-line"}
        markerEnd={edge.suspicious ? "url(#arrow-risk)" : "url(#arrow)"}
        onClick={onSelect}
        onKeyDown={activate}
        role="button"
        tabIndex={0}
        x1={source.x}
        x2={target.x}
        y1={source.y}
        y2={target.y}
      />
      <text className="edge-label" textAnchor="middle" x={midX} y={midY - 9}>
        {edge.label}
      </text>
      {edge.detail ? (
        <text className="edge-detail" textAnchor="middle" x={midX} y={midY + 9}>
          {edge.detail}
        </text>
      ) : null}
      {provenanceVisible ? (
        <g className={selected ? "provenance-anchor selected" : "provenance-anchor"}>
          <circle cx={midX + 48} cy={midY - 12} r="8" />
          <text textAnchor="middle" x={midX + 48} y={midY - 9}>
            {edge.evidenceIds.length}
          </text>
        </g>
      ) : null}
    </g>
  );
}

export function GraphCanvas({ selectedEdgeId, onSelectEdge }: GraphCanvasProps) {
  const [view, setView] = useState<"Graph" | "Flow" | "Table">("Graph");
  const [hops, setHops] = useState(3);
  const [provenanceVisible, setProvenanceVisible] = useState(true);
  const legend = useMemo(
    () =>
      (Object.entries(colors) as [EntityKind, string][]).map(([kind, color]) => (
        <span className="legend-item" key={kind}>
          <i style={{ backgroundColor: color }} />
          {kind}
        </span>
      )),
    [],
  );

  return (
    <section aria-label="Entity graph" className="graph-panel panel">
      <div className="panel-toolbar">
        <div className="segmented" aria-label="Investigation view">
          {(["Graph", "Flow", "Table"] as const).map((mode) => (
            <button
              aria-pressed={view === mode}
              className={view === mode ? "active" : ""}
              key={mode}
              onClick={() => setView(mode)}
              type="button"
            >
              {mode}
            </button>
          ))}
        </div>
        <div className="graph-filters">
          <button
            aria-label="Change graph depth"
            className="control"
            onClick={() => setHops((current) => (current === 3 ? 1 : current + 1))}
            type="button"
          >
            <Route size={14} /> {hops} hops
          </button>
          <button className="control" type="button"><Layers3 size={14} /> All layers</button>
          <button
            aria-pressed={provenanceVisible}
            className="control provenance"
            onClick={() => setProvenanceVisible((visible) => !visible)}
            type="button"
          >
            {provenanceVisible ? <Eye size={14} /> : <EyeOff size={14} />}
            {provenanceVisible ? "Provenance on" : "Provenance hidden"}
          </button>
          <button className="icon-button" aria-label="Full screen" type="button">
            <Maximize2 size={15} />
          </button>
        </div>
      </div>
      <div className="graph-stage">
        <div className="graph-stage-meta">
          <span><ScanSearch size={13} /> Entity resolution 98.7%</span>
          <span><i /> Risk layer live</span>
        </div>
        <div className="legend">{legend}</div>
        <svg aria-label="Financial relationship network" viewBox="0 0 1020 510">
          <defs>
            <filter id="node-glow" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            <marker id="arrow" markerHeight="6" markerWidth="6" orient="auto" refX="6" refY="3">
              <path d="M0,0 L0,6 L6,3 z" fill="#607084" />
            </marker>
            <marker id="arrow-risk" markerHeight="6" markerWidth="6" orient="auto" refX="6" refY="3">
              <path d="M0,0 L0,6 L6,3 z" fill="#ff8c42" />
            </marker>
          </defs>
          {edges.map((edge) => (
            <Edge
              edge={edge}
              key={edge.id}
              onSelect={() => onSelectEdge(edge.id)}
              provenanceVisible={provenanceVisible}
              selected={selectedEdgeId === edge.id}
            />
          ))}
          {nodes.map((node) => (
            <g className={node.risk ? "graph-node risk" : "graph-node"} key={node.id}>
              <circle
                className="node-shell"
                cx={node.x}
                cy={node.y}
                fill="#101722"
                r="31"
                stroke={colors[node.kind]}
              />
              <circle cx={node.x} cy={node.y} fill={colors[node.kind]} opacity=".13" r="23" />
              <text className="node-mark" textAnchor="middle" x={node.x} y={node.y + 5}>
                {node.kind === "person" ? "P" : node.kind === "wallet" ? "W" : "●"}
              </text>
              <text className="node-label" textAnchor="middle" x={node.x} y={node.y + 50}>
                {node.label}
              </text>
              <text className="node-detail" textAnchor="middle" x={node.x} y={node.y + 66}>
                {node.detail}
              </text>
              {node.risk ? <circle className="risk-pulse" cx={node.x + 25} cy={node.y - 22} r="6" /> : null}
            </g>
          ))}
        </svg>
        <div className="zoom-controls" aria-label="Graph zoom controls">
          <button aria-label="Zoom in" type="button"><Plus size={16} /></button>
          <button aria-label="Center graph" type="button"><Crosshair size={15} /></button>
          <button aria-label="Zoom out" type="button"><Minus size={16} /></button>
        </div>
        <div className="minimap" aria-hidden="true">
          <div className="minimap-viewport" />
          <span /><span /><span /><span /><span />
        </div>
        <div className="graph-footnote">
          <span>42 entities</span><i /><span>118 relationships</span><i /><span>29 evidence anchors</span>
        </div>
      </div>
    </section>
  );
}
