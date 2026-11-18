# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

ArchHypo Flow currently ships as a Tauri desktop app with a React interface for use in the master's research. Desktop is the current delivery target, not a limit on the pattern: future contributors can extend it to web, mobile, or other clients.

## Users

Software architects and technical leads who need to investigate an unresolved architectural decision before committing to an approach.

## Product Purpose

ArchHypo Flow helps practitioners turn an architectural uncertainty into a testable hypothesis and a short technical plan. Success means the practitioner has a concrete claim they can evaluate and a plan for deciding what to do next.

## Positioning

ArchHypo Flow implements the ArchHypo technique as a structured workflow rather than leaving the reasoning in an unstructured chat transcript. It separates discovery, hypothesis formulation, assessment, and technical planning so that intermediate results can be reviewed and revised.

## Operating Context

Practitioners describe an uncertainty in natural language. The agent can ask for missing context and propose a hypothesis. By default, practitioners review the hypothesis before assessment and review the assessment and plan before the final response. They can reject a proposal with a reason and continue with a revised result. Conversations and pending reviews can be resumed from local history.

## Capabilities and Constraints

- Human approval is enabled by default and can be disabled. Skipping review does not create approval records.
- The desktop interface supports English and Brazilian Portuguese, including application-authored accessible labels.
- The desktop app and CLI share local SQLite storage. A local backend does not imply offline model inference; chat uses configured model services.
- Web and mobile are extension possibilities, not current deliverables. No future client stack has been selected here.

## Brand Commitments

ArchHypo Flow is the product name. ArchHypo names the technique it implements.

## Evidence on Hand

- [`docs/archhypo-flow.md`](docs/archhypo-flow.md) describes the workflow and approval gates.
- [`apps/archhypo-flow-desktop/README.md`](apps/archhypo-flow-desktop/README.md) documents desktop behavior, language support, and development commands.
- [`contracts/agent-stream.schema.json`](contracts/agent-stream.schema.json) defines the shared event contract.

## Product Principles

- Start from the practitioner's architectural uncertainty; ask when essential context is missing.
- Produce a claim that can be tested and a plan the practitioner can review.
- Keep human decisions distinguishable from generated results.
- Keep the workflow reusable beyond the first desktop interface.
