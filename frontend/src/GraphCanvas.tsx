import { Maximize2, Minus, Plus, Route } from "lucide-react";
import { useMemo } from "react";

import { edges, nodes } from "./demo";
import type { EntityKind, GraphEdge, GraphNode } from "./types";

const colors: Record<EntityKind, string> = {
  company: "#5bc8ff",
  person: "#b48cff",
  account: "#4fd7a8",
  wallet: "#ffb547",
  jurisdiction: "#ff6b6b",
  service: "#8a98aa",
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

function Edge({ edge, selected, onSelect }: {
  edge: GraphEdge;
  selected: boolean;
  onSelect: () => void;
}) {
  const source = endpoint(edge.source);
  const target = endpoint(edge.target);
  const midX = (source.x + target.x) / 2;
  const midY = (source.y + target.y) / 2;

  return (
    <g className={edge.suspicious ? "graph-edge suspicious" : "graph-edge"}>
      <line
        aria-label={`${source.label} to ${target.label}: ${edge.label}`}
        className={selected ? "edge-line selected" : "edge-line"}
        markerEnd={edge.suspicious ? "url(#arrow-risk)" : "url(#arrow)"}
        onClick={onSelect}
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
    </g>
  );
}

export function GraphCanvas({ selectedEdgeId, onSelectEdge }: GraphCanvasProps) {
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
        <div className="segmented" aria-label="Graph view">
          <button className="active" type="button">Entity graph</button>
          <button type="button">Table</button>
          <button type="button">Map</button>
        </div>
        <div className="graph-filters">
          <button className="control" type="button"><Route size={14} /> 3 hops</button>
          <button className="control" type="button">All entities</button>
          <button className="control provenance" type="button"><span /> Provenance on</button>
          <button className="icon-button" aria-label="Full screen" type="button">
            <Maximize2 size={15} />
          </button>
        </div>
      </div>
      <div className="graph-stage">
        <div className="legend">{legend}</div>
        <svg aria-label="Financial relationship network" viewBox="0 0 1020 510">
          <defs>
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
              selected={selectedEdgeId === edge.id}
            />
          ))}
          {nodes.map((node) => (
            <g className={node.risk ? "graph-node risk" : "graph-node"} key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                fill="#101722"
                r="31"
                stroke={colors[node.kind]}
              />
              <circle cx={node.x} cy={node.y} fill={colors[node.kind]} opacity=".16" r="23" />
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
          <button aria-label="Zoom out" type="button"><Minus size={16} /></button>
        </div>
        <div className="minimap" aria-hidden="true">
          <span /><span /><span /><span /><span />
        </div>
      </div>
    </section>
  );
}
