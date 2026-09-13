# agent-stream-py

Python models and serializers for the ArchWise agent stream protocol.

```python
from agent_stream_py import agent_event_data, text_delta_event

payload = agent_event_data(
    text_delta_event(run_id="run-1", thread_id="thread-1", text="Hi")
)
```

The wire contract lives in `contracts/agent-stream.schema.json`.
