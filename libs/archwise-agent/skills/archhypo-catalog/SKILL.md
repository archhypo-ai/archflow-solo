---
name: archhypo-catalog
description: Catalog of the 12 ArchHypo architecture decision and validation patterns. Load this skill during the technical plan step to select the most suitable pattern for reducing an architectural uncertainty. For each pattern there is a detailed reference file; read the relevant one before proposing a pattern.
---

# ArchHypo Catalog

## Overview

The official ArchHypo pattern catalog. It contains exactly 12 patterns used to reduce architectural uncertainty through experiments, inspections, and guided decisions. Always select a pattern from this catalog, never invent a pattern or pick one from memory without consulting this catalog.

## How to use this skill

This skill uses progressive disclosure: SKILL.md lists each pattern and when to use it, while the full pattern descriptions live in `references/`. Once you pick a pattern for a technical plan item, read its reference file to ground your suggestion (problem, forces, solution, consequences, related patterns, concrete examples), do not rely on memory.

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

Each reference documents one pattern in full (AKA, problem, forces, solution, consequences, related patterns, examples). Some files are long (e.g., `Continuous_Inspection.md` is ~20KB), scan the section headers first and jump to the part that matters for the current plan item instead of reading linearly.
