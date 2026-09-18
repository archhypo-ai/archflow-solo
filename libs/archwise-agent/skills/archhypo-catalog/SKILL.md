---
name: archhypo-catalog
description: Catalog of the 12 ArchHypo architecture decision and validation patterns. Load this skill during the technical plan step to select relevant candidates and use the governed catalog reader to consult references before proposing a pattern.
---

# ArchHypo Catalog

## Overview

The official ArchHypo pattern catalog. It contains exactly 12 patterns used to reduce architectural uncertainty through experiments, inspections, and guided decisions. Always select a pattern from this catalog, never invent a pattern or pick one from memory without consulting this catalog.

## How to use this skill

This skill uses progressive disclosure: the index below is used to select
candidates, while full descriptions remain in `references/`. Access full
references only through the `read_archhypo_catalog` tool. Do not enumerate the
reference directory or construct paths yourself.

Follow this protocol:

1. Screen all patterns using the `Use when` column.
2. Request the most relevant primary patterns through `read_archhypo_catalog`.
   The final answer must contain three to five items, but exploration may read
   more patterns when the uncertainty is broad.
3. Treat `Related Patterns` as one-hop suggestions. Request a related pattern
   only if it belongs to this catalog and could change the plan.
4. Stop when the evidence is sufficient or the reader reports its context
   budget. The reader automatically skips patterns already loaded during the
   current graph execution.
5. Ground the final three-to-five plan items in the returned references.

If the uncertainty is broad, set `read_all=true`. The reader may load the whole
catalog once; the final answer is still limited to three to five items.

## The 12 patterns

| # | Pattern | Use when | Reference |
|---|---|---|---|
| 1 | Architectural Spike | There is technical uncertainty about an architectural solution; a minimal temporary implementation can explore feasibility of a technology or approach. | `references/Architecture_Spike.md` |
| 2 | Architectural Trigger | An event or change (requirements, scaling needs, new regulations, emerging technologies) may require the team to reassess architectural decisions. | `references/Architecture_Trigger.md` |
| 3 | Bring the Specialist | The team faces a complex architectural decision or lacks expertise; involving a specialist keeps the decision well-founded and reduces technical risk. | `references/Bring_the_Specialist.md` |
| 4 | Continuous Inspection | The architecture and code should be reviewed continuously so deviations, emerging risks, and improvement opportunities are spotted early. | `references/Continuous_Inspection.md` |
| 5 | Learning from Experiments | An architectural decision should be preceded by controlled experiments that generate real data and insights. | `references/Learning_from_Experiments.md` |
| 6 | Plan for Preparation | Future decisions are not yet mature, but the architecture can be prepared now with flexibility, modularity, and abstractions that make later changes cheap. | `references/Plan_for_Preparation.md` |
| 7 | Postpone Uncertain Decisions | A decision involves many unknowns or high risk; postponing it avoids premature choices and allows incremental learning. | `references/Postpone_Uncertain_Decisions.md` |
| 8 | Protective Guideline | The project needs guardrails that protect the architecture from inconsistent decisions, inadequate techniques, or standard violations. | `references/Protective_Guideline.md` |
| 9 | Quality Checkpoint | There should be specific moments to assess whether the architecture meets defined quality attributes (performance, security, scalability). | `references/Quality_Checkpoint.md` |
| 10 | Software Analytics (What You Need to Know) | A knowledge gap blocks an architectural decision; the team must define the key questions and seek the critical information to answer them. | `references/What_you_Need_to_Know.md` |
| 11 | Technical Debt Management | Technical debt must be identified, prioritized, and mitigated so it does not hinder architectural evolution. | `references/Technical_Debt_Management.md` |
| 12 | Tracer Bullets | Minimal end-to-end implementations can validate flows, integrations, and the overall architecture before full development. | `references/Tracer_Bullets.md` |

## Reading the references

`read_archhypo_catalog` resolves the exact path from this index and returns the
reference content without exposing filesystem traversal. It deduplicates reads
per graph execution and enforces a context-size budget. Related-pattern sections
are evidence for candidate selection, not recursive navigation instructions.
