export type ArtifactPlanItem = {
  title: string;
  pattern: string;
};

export type ArtifactSummary = {
  id: string;
  cycleId: string;
  threadId: string;
  projectId: string | null;
  title: string;
  status: string;
  outcome: string;
  uncertainty: string;
  hypothesisStatement: string;
  nfr: string | null;
  impact: string | null;
  uncertaintyLevel: string | null;
  technicalPlanItems: ArtifactPlanItem[];
  createdAt: string;
};
