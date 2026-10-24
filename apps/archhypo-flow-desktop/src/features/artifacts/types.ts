export type ArtifactPlanItem = {
  title: string;
  pattern: string;
};

export type ArtifactStatus = "open" | "closed";

export type ArtifactSummary = {
  id: string;
  cycleId: string;
  threadId: string;
  projectId: string | null;
  title: string;
  status: ArtifactStatus;
  outcome: string;
  uncertainty: string;
  hypothesisStatement: string;
  nfr: string | null;
  impact: string | null;
  uncertaintyLevel: string | null;
  technicalPlanItems: ArtifactPlanItem[];
  createdAt: string;
};

export type ArtifactDetail = {
  id: string;
  cycleId: string;
  threadId: string;
  projectId: string | null;
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
    nfrJustification: string;
    impact: string;
    impactJustification: string;
    uncertainty: string;
    uncertaintyJustification: string;
  };
  technicalPlan: {
    rationale: string;
    items: Array<{
      title: string;
      objective: string;
      description: string;
      pattern: string;
      tradeoff: string;
    }>;
  };
  createdAt: string;
  updatedAt: string;
};
