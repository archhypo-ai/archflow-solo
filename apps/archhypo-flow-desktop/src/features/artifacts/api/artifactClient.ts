import type {
  ArtifactDetail,
  ArtifactReviewHistoryEntry,
  ArtifactStatus,
  ArtifactSummary,
} from "../types";

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
  status: ArtifactStatus;
  outcome: string;
  uncertainty: string;
  hypothesis_statement: string;
  nfr: string | null;
  impact: string | null;
  uncertainty_level: string | null;
  technical_plan_items: BackendArtifactPlanItem[];
  created_at: string;
};

type BackendArtifactDetail = {
  id: string;
  cycle_id: string;
  thread_id: string;
  project_id: string | null;
  title: string;
  status: ArtifactStatus;
  outcome: string;
  uncertainty: string;
  hypothesis: {
    title: string;
    statement: string;
    justification: string;
  };
  assessment: {
    nfr: string;
    nfr_justification: string;
    impact: string;
    impact_justification: string;
    uncertainty: string;
    uncertainty_justification: string;
  };
  technical_plan: {
    rationale: string;
    items: Array<{
      title: string;
      objective: string;
      description: string;
      pattern: string;
      tradeoff: string;
    }>;
  };
  review_history?: ArtifactReviewHistoryEntry[];
  created_at: string;
  updated_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

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

  return (await response.json()) as T;
}

export async function listArtifacts(): Promise<ArtifactSummary[]> {
  const artifacts = await request<BackendArtifactSummary[]>("/api/artifacts");
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

export async function getArtifact(artifactId: string): Promise<ArtifactDetail> {
  return toArtifactDetail(
    await request<BackendArtifactDetail>(
      `/api/artifacts/${encodeURIComponent(artifactId)}`,
    ),
  );
}

export async function updateArtifactStatus(
  artifactId: string,
  status: ArtifactStatus,
): Promise<ArtifactDetail> {
  const artifact = await request<BackendArtifactDetail>(
    `/api/artifacts/${encodeURIComponent(artifactId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ status }),
    },
  );
  return toArtifactDetail(artifact);
}

function toArtifactDetail(artifact: BackendArtifactDetail): ArtifactDetail {
  return {
    id: artifact.id,
    cycleId: artifact.cycle_id,
    threadId: artifact.thread_id,
    projectId: artifact.project_id,
    title: artifact.title,
    status: artifact.status,
    outcome: artifact.outcome,
    uncertainty: artifact.uncertainty,
    hypothesis: artifact.hypothesis,
    assessment: {
      nfr: artifact.assessment.nfr,
      nfrJustification: artifact.assessment.nfr_justification,
      impact: artifact.assessment.impact,
      impactJustification: artifact.assessment.impact_justification,
      uncertainty: artifact.assessment.uncertainty,
      uncertaintyJustification: artifact.assessment.uncertainty_justification,
    },
    technicalPlan: artifact.technical_plan,
    reviewHistory: artifact.review_history ?? [],
    createdAt: artifact.created_at,
    updatedAt: artifact.updated_at,
  };
}
