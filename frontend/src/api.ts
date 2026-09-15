import type { ApiCase, InvestigationRun } from "./types";

function headers(): HeadersInit {
  const token = window.sessionStorage.getItem("evidencegraph.access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { ...headers(), ...init?.headers },
  });
  if (!response.ok) throw new Error(`EvidenceGraph API returned ${response.status}`);
  return (await response.json()) as T;
}

export function listCases(): Promise<ApiCase[]> {
  return request<ApiCase[]>("/api/v1/cases?limit=25&offset=0");
}

export function startInvestigation(caseId: string): Promise<InvestigationRun> {
  return request<InvestigationRun>(`/api/v1/cases/${caseId}/investigations`, {
    method: "POST",
  });
}

export function getInvestigationRun(runId: string): Promise<InvestigationRun> {
  return request<InvestigationRun>(`/api/v1/investigation-runs/${runId}`);
}
