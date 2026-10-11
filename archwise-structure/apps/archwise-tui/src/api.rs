use std::io::BufReader;
use std::time::Duration;

pub use agent_stream_rust::AgentEvent;
use agent_stream_rust::SseDecoder;
use color_eyre::eyre::{eyre, Result, WrapErr};
use reqwest::blocking::{Client, Response};
use serde::{Deserialize, Serialize};

pub const DEFAULT_BACKEND_URL: &str = "http://127.0.0.1:8765";
pub const REQUIRED_BACKEND_API_VERSION: &str = env!("ARCHWISE_BACKEND_API_VERSION");

#[derive(Clone)]
pub struct BackendClient {
    client: Client,
    base_url: String,
}

#[derive(Debug, Serialize)]
struct ChatRequest<'a> {
    thread_id: &'a str,
    message: &'a str,
    run_id: &'a str,
}

#[derive(Debug, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub agent_ready: bool,
    pub api_version: Option<String>,
    pub sse_chat: Option<bool>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct ThreadSummary {
    pub thread_id: String,
    pub title: String,
    pub message_count: usize,
}

#[derive(Debug, Deserialize)]
pub struct ThreadMessage {
    pub role: String,
    pub content: String,
}

#[derive(Debug, Deserialize)]
pub struct ThreadResponse {
    pub thread_id: String,
    pub title: String,
    pub message_count: usize,
    pub messages: Vec<ThreadMessage>,
}

pub type ChatStream = SseDecoder<BufReader<Response>>;

impl BackendClient {
    pub fn new(base_url: impl Into<String>) -> Result<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(180))
            .build()
            .wrap_err("Could not build HTTP client")?;
        Ok(Self {
            client,
            base_url: base_url.into().trim_end_matches('/').to_owned(),
        })
    }

    pub fn health(&self) -> Result<HealthResponse> {
        self.request_json(
            self.client
                .get(format!("{}/api/health", self.base_url))
                .timeout(Duration::from_secs(2)),
        )
    }

    pub fn list_threads(&self) -> Result<Vec<ThreadSummary>> {
        self.request_json(self.client.get(format!("{}/api/threads", self.base_url)))
    }

    pub fn get_thread(&self, thread_id: &str) -> Result<ThreadResponse> {
        self.request_json(
            self.client
                .get(format!("{}/api/threads/{thread_id}", self.base_url)),
        )
    }

    pub fn send_message_stream(
        &self,
        thread_id: &str,
        message: &str,
        run_id: &str,
    ) -> Result<ChatStream> {
        let response = self
            .client
            .post(format!("{}/api/chat/stream", self.base_url))
            .header("Accept", "text/event-stream")
            .json(&ChatRequest {
                thread_id,
                message,
                run_id,
            })
            .send()
            .wrap_err("Could not reach ArchWise backend")?;
        let status = response.status();
        if !status.is_success() {
            let body = response
                .text()
                .wrap_err("Could not read backend response")?;
            return Err(eyre!("Backend returned HTTP {status}: {body}"));
        }

        Ok(SseDecoder::from_reader(BufReader::new(response)))
    }

    pub fn cancel_run(&self, run_id: &str) -> Result<bool> {
        let response = self
            .client
            .post(format!("{}/api/chat/runs/{run_id}/cancel", self.base_url))
            .send()
            .wrap_err("Could not reach ArchWise backend")?;
        let status = response.status();
        let body = response
            .text()
            .wrap_err("Could not read backend response")?;
        if !status.is_success() {
            return Err(eyre!("Backend returned HTTP {status}: {body}"));
        }

        let payload: ChatCancelResponse =
            serde_json::from_str(&body).wrap_err("Invalid cancel response")?;
        Ok(payload.cancelled)
    }

    pub fn delete_thread(&self, thread_id: &str) -> Result<()> {
        let response = self
            .client
            .delete(format!("{}/api/threads/{thread_id}", self.base_url))
            .send()
            .wrap_err("Could not reach ArchWise backend")?;
        let status = response.status();
        let body = response
            .text()
            .wrap_err("Could not read backend response")?;

        if !status.is_success() {
            return Err(eyre!("Backend returned HTTP {status}: {body}"));
        }

        Ok(())
    }

    fn request_json<T>(&self, request: reqwest::blocking::RequestBuilder) -> Result<T>
    where
        T: for<'de> Deserialize<'de>,
    {
        let response = request
            .send()
            .wrap_err("Could not reach ArchWise backend")?;
        let status = response.status();
        let body = response
            .text()
            .wrap_err("Could not read backend response")?;

        if !status.is_success() {
            return Err(eyre!("Backend returned HTTP {status}: {body}"));
        }

        serde_json::from_str(&body).wrap_err("Invalid backend response")
    }
}

#[derive(Debug, Deserialize)]
struct ChatCancelResponse {
    cancelled: bool,
}
