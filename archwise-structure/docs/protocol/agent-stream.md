# Agent stream protocol

ArchWise clients consume one agent run through Server-Sent Events (SSE).
The protocol is transport-facing, not UI-facing. Tools, HITL interrupts, and
subagents use the same event stream.

## Wire format

Every SSE frame uses event name `archwise` and contains one JSON object in its
`data` field:

```text
event: archwise
data: {"protocol_version":1,"run_id":"run-123","thread_id":"thread-456","type":"text_delta","text":"Hello"}
```

`contracts/agent-stream.schema.json` is the source of truth for the JSON
payload. Clients do not load this file at runtime. They parse the JSON in each
`data` field.

## Common fields

- `protocol_version`: wire protocol version, independent from project version;
- `run_id`: one execution attempt;
- `thread_id`: persistent conversation checkpoint;
- `type`: discriminant for the event payload.

## Event types

Current events:

- `phase`;
- `text_delta`;
- `done`;
- `cancelled`;
- `error`;
- `tool_call_start`;
- `tool_call_delta`;
- `tool_result`.

`interrupt` remains reserved for future human-in-the-loop workflows.

Python, Rust, and TypeScript SDKs provide language-native models and SSE
framing/parsing. They must not contain agent orchestration or UI behavior.
