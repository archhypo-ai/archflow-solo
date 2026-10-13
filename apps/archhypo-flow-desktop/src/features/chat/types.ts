type ChatStreamEventBase = {
  protocol_version: 1;
  run_id: string;
  thread_id: string;
};

export type HumanReviewDecision = {
  decision: "approved" | "rejected";
  reason?: string;
};

export type HypothesisReviewDecision = HumanReviewDecision;
export type TechnicalPlanReviewDecision = HumanReviewDecision;

export type PendingHypothesisReview = {
  kind: "hypothesis_review";
  hypothesis: {
    uncertainty: string;
    title: string;
    statement: string;
    justification: string;
  };
};

export type AssessmentLevel = "Very Low" | "Low" | "Medium" | "High" | "Very High";

export type PendingTechnicalPlanReview = {
  kind: "technical_plan_review";
  assessment: {
    impact: AssessmentLevel;
    impact_justification: string;
    uncertainty: AssessmentLevel;
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
};

export type PendingHumanReview =
  | PendingHypothesisReview
  | PendingTechnicalPlanReview;

export type CompletedHumanReview =
  | {
      kind: "hypothesis_review";
      review: PendingHypothesisReview;
      decision: HumanReviewDecision;
      after_message_count: number;
    }
  | {
      kind: "technical_plan_review";
      review: PendingTechnicalPlanReview;
      decision: HumanReviewDecision;
      after_message_count: number;
    };

export type ChatStreamEvent =
  | (ChatStreamEventBase & {
      type: "conversation_started";
      title: string;
      user_message: string;
      project_id: string | null;
    })
  | (ChatStreamEventBase & {
      type: "phase";
      phase: "thinking" | "answering";
    })
  | (ChatStreamEventBase & {
      type: "tool_call_start";
      tool_call_id: string;
      name: string;
    })
  | (ChatStreamEventBase & {
      type: "tool_call_delta";
      tool_call_id: string;
      text: string;
    })
  | (ChatStreamEventBase & {
      type: "tool_result";
      tool_call_id: string;
      output: unknown;
      is_error: boolean;
    })
  | (ChatStreamEventBase & { type: "text_delta"; text: string })
  | (ChatStreamEventBase & {
      type: "interrupt";
      interrupt_id: string;
      message: string;
      payload: PendingHumanReview | null;
    })
  | (ChatStreamEventBase & {
      type: "done";
      status: "completed";
      title: string;
      message: string;
    })
  | (ChatStreamEventBase & { type: "error"; message: string });
