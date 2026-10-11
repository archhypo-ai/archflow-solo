use serde::Deserialize;

#[derive(Debug, Deserialize, Clone, PartialEq)]
#[serde(tag = "type")]
pub enum AgentEvent {
    #[serde(rename = "phase")]
    Phase {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        phase: String,
    },
    #[serde(rename = "text_delta")]
    TextDelta {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        text: String,
    },
    #[serde(rename = "done")]
    Done {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        status: String,
    },
    #[serde(rename = "cancelled")]
    Cancelled {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        status: String,
        reason: Option<String>,
    },
    #[serde(rename = "error")]
    Error {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        message: String,
    },
    #[serde(rename = "tool_call_start")]
    ToolCallStart {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        tool_call_id: String,
        name: String,
    },
    #[serde(rename = "tool_call_delta")]
    ToolCallDelta {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        tool_call_id: String,
        text: String,
    },
    #[serde(rename = "tool_result")]
    ToolResult {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        tool_call_id: String,
        output: serde_json::Value,
        #[serde(default)]
        is_error: bool,
    },
    #[serde(rename = "interrupt")]
    Interrupt {
        protocol_version: u8,
        run_id: String,
        thread_id: String,
        interrupt_id: String,
        message: String,
        payload: Option<serde_json::Map<String, serde_json::Value>>,
    },
}
