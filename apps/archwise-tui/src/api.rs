use std::time::Duration;

use color_eyre::eyre::{eyre, Result, WrapErr};
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};

pub const DEFAULT_BACKEND_URL: &str = "http://127.0.0.1:8765";

#[derive(Clone)]
pub struct BackendClient {
    client: Client,
    base_url: String,
}

#[derive(Debug, Serialize)]
struct ChatRequest<'a> {
    thread_id: &'a str,
    message: &'a str,
}

#[derive(Debug, Deserialize)]
pub struct ChatResponse {
    pub message: String,
}

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

    pub fn send_message(&self, thread_id: &str, message: &str) -> Result<ChatResponse> {
        let response = self
            .client
            .post(format!("{}/api/chat", self.base_url))
            .json(&ChatRequest { thread_id, message })
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
