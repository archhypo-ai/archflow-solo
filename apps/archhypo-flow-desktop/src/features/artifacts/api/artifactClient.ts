import type { ArtifactSummary } from "../types";

const API_BASE_URL = "http://127.0.0.1:8765";

type BackendArtifactPlanItem = {
  title: string;
  pattern: string;
};

type BackendArtifactSummary = {
  id: string;
  cycle_id: string;
  thread_id: string;
  project_id: string | null;
  title: string;
  status: string;
  outcome: string;
  uncertainty: string;
  hypothesis_statement: string;
  nfr: string | null;
  impact: string | null;
  uncertainty_level: string | null;
  technical_plan_items: BackendArtifactPlanItem[];
  created_at: string;
};

export async function listArtifacts(): Promise<ArtifactSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/artifacts`);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Keep the HTTP status text when the error body is not JSON.
    }
    throw new Error(`Artifact API error (${response.status}): ${detail}`);
  }

  const artifacts = (await response.json()) as BackendArtifactSummary[];
  return artifacts.map((artifact) => ({
    id: artifact.id,
    cycleId: artifact.cycle_id,
    threadId: artifact.thread_id,
    projectId: artifact.project_id,
    title: artifact.title,
    status: artifact.status,
    outcome: artifact.outcome,
    uncertainty: artifact.uncertainty,
    hypothesisStatement: artifact.hypothesis_statement,
    nfr: artifact.nfr,
    impact: artifact.impact,
    uncertaintyLevel: artifact.uncertainty_level,
    technicalPlanItems: artifact.technical_plan_items,
    createdAt: artifact.created_at,
  }));
}
