export type EntityKind =
  | "company"
  | "person"
  | "account"
  | "wallet"
  | "jurisdiction"
  | "service";

export interface GraphNode {
  id: string;
  label: string;
  detail: string;
  kind: EntityKind;
  x: number;
  y: number;
  risk?: boolean;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  detail?: string;
  suspicious?: boolean;
}

export interface EvidenceItem {
  id: string;
  title: string;
  source: string;
  date: string;
  hash: string;
  locator: string;
}

export interface TimelineEvent {
  id: string;
  time: string;
  date: string;
  title: string;
  detail: string;
  kind: "transaction" | "document" | "ai" | "risk" | "review";
}
