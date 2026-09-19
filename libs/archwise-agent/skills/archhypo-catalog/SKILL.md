---
name: archhypo-catalog
description: Catalog of the 12 ArchHypo architecture decision and validation patterns. Load this skill during the technical plan step to select relevant candidates and use the governed catalog reader to consult references before proposing a pattern.
---

# ArchHypo Catalog

## The 12 patterns

| # | Pattern | Use when | Related official patterns | Reference |
|---|---|---|---|---|
| 1 | Architectural Spike | There is technical uncertainty about an architectural solution; a minimal temporary implementation can explore feasibility of a technology or approach. | Bring the Specialist; Technical Debt Management; Tracer Bullets | `references/Architecture_Spike.md` |
| 2 | Architectural Trigger | An event or change (requirements, scaling needs, new regulations, emerging technologies) may require the team to reassess architectural decisions. | Architectural Spike; Continuous Inspection; Quality Checkpoint; Technical Debt Management | `references/Architecture_Trigger.md` |
| 3 | Bring the Specialist | The team faces a complex architectural decision or lacks expertise; involving a specialist keeps the decision well-founded and reduces technical risk. | Architectural Spike; Plan for Preparation; Tracer Bullets | `references/Bring_the_Specialist.md` |
| 4 | Continuous Inspection | The architecture and code should be reviewed continuously so deviations, emerging risks, and improvement opportunities are spotted early. | Architectural Trigger; Protective Guideline; Technical Debt Management | `references/Continuous_Inspection.md` |
| 5 | Learning from Experiments | An architectural decision should be preceded by controlled experiments that generate real data and insights. | Software Analytics (What You Need to Know) | `references/Learning_from_Experiments.md` |
| 6 | Plan for Preparation | Future decisions are not yet mature, but the architecture can be prepared now with flexibility, modularity, and abstractions that make later changes cheap. | Bring the Specialist; Architectural Spike; Software Analytics (What You Need to Know) | `references/Plan_for_Preparation.md` |
| 7 | Postpone Uncertain Decisions | A decision involves many unknowns or high risk; postponing it avoids premature choices and allows incremental learning. | Architectural Trigger | `references/Postpone_Uncertain_Decisions.md` |
| 8 | Protective Guideline | The project needs guardrails that protect the architecture from inconsistent decisions, inadequate techniques, or standard violations. | Continuous Inspection; Quality Checkpoint | `references/Protective_Guideline.md` |
| 9 | Quality Checkpoint | There should be specific moments to assess whether the architecture meets defined quality attributes (performance, security, scalability). | Architectural Trigger; Protective Guideline | `references/Quality_Checkpoint.md` |
| 10 | Software Analytics (What You Need to Know) | A knowledge gap blocks an architectural decision; the team must define the key questions and seek the critical information to answer them. | Learning from Experiments; Plan for Preparation | `references/What_you_Need_to_Know.md` |
| 11 | Technical Debt Management | Technical debt must be identified, prioritized, and mitigated so it does not hinder architectural evolution. | Architectural Spike; Architectural Trigger; Continuous Inspection | `references/Technical_Debt_Management.md` |
| 12 | Tracer Bullets | Minimal end-to-end implementations can validate flows, integrations, and the overall architecture before full development. | Architectural Spike; Bring the Specialist | `references/Tracer_Bullets.md` |
