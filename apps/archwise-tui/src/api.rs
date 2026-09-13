use std::io::{BufRead, BufReader};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;

use color_eyre::eyre::{eyre, Result, WrapErr};
use reqwest::blocking::{Client, Response};
use serde::{de::DeserializeOwned, Deserialize, Serialize};

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

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ChatStreamEvent {
    Phase { phase: String },
    Delta { text: String },
    Done,
    Cancelled,
    Error { message: String },
}

pub struct ChatStream {
    reader: Box<dyn BufRead + Send>,
    event_type: Option<String>,
    data_lines: Vec<String>,
}

impl ChatStream {
    fn from_response(response: Response) -> Self {
        Self::from_reader(BufReader::new(response))
    }

    fn from_reader<R>(reader: R) -> Self
    where
        R: BufRead + Send + 'static,
    {
        Self {
            reader: Box::new(reader),
            event_type: None,
            data_lines: Vec::new(),
        }
    }

    fn dispatch_pending(&mut self) -> Option<Result<ChatStreamEvent>> {
        let event_type = self
            .event_type
            .take()
            .unwrap_or_else(|| String::from("message"));
        let data = std::mem::take(&mut self.data_lines).join("\n");
        if data.is_empty() {
            return None;
        }

        match decode_event(&event_type, &data) {
            Ok(Some(event)) => Some(Ok(event)),
            Ok(None) => None,
            Err(error) => Some(Err(error)),
        }
    }
}

impl ChatStream {
    pub fn next_with_cancellation(
        &mut self,
        cancellation: &AtomicBool,
    ) -> Option<Result<ChatStreamEvent>> {
        self.next_event(Some(cancellation))
    }

    fn next_event(&mut self, cancellation: Option<&AtomicBool>) -> Option<Result<ChatStreamEvent>> {
        loop {
            if cancellation.is_some_and(|token| token.load(Ordering::Relaxed)) {
                return None;
            }
            let mut line = String::new();
            match self.reader.read_line(&mut line) {
                Ok(0) => {
                    if self.event_type.is_some() || !self.data_lines.is_empty() {
                        if let Some(event) = self.dispatch_pending() {
                            return Some(event);
                        }
                    }
                    return None;
                }
                Ok(_) => {}
                Err(error) if error.kind() == std::io::ErrorKind::TimedOut => continue,
                Err(error) => return Some(Err(error.into())),
            }

            let line = line.trim_end_matches(&['\r', '\n'][..]);
            if line.is_empty() {
                if let Some(event) = self.dispatch_pending() {
                    return Some(event);
                }
                continue;
            }
            if line.starts_with(':') {
                continue;
            }

            let Some((field, value)) = line.split_once(':') else {
                continue;
            };
            let value = value.strip_prefix(' ').unwrap_or(value);
            match field {
                "event" => self.event_type = Some(value.to_owned()),
                "data" => self.data_lines.push(value.to_owned()),
                _ => {}
            }
        }
    }
}

impl Iterator for ChatStream {
    type Item = Result<ChatStreamEvent>;

    fn next(&mut self) -> Option<Self::Item> {
        self.next_event(None)
    }
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

        Ok(ChatStream::from_response(response))
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

fn decode_event(event_type: &str, data: &str) -> Result<Option<ChatStreamEvent>> {
    match event_type {
        "phase" => {
            let payload: PhasePayload = parse_event_payload(event_type, data)?;
            Ok(Some(ChatStreamEvent::Phase {
                phase: payload.phase,
            }))
        }
        "delta" => {
            let payload: DeltaPayload = parse_event_payload(event_type, data)?;
            Ok(Some(ChatStreamEvent::Delta { text: payload.text }))
        }
        "done" => Ok(Some(ChatStreamEvent::Done)),
        "cancelled" => Ok(Some(ChatStreamEvent::Cancelled)),
        "error" => {
            let payload: ErrorPayload = parse_event_payload(event_type, data)?;
            Ok(Some(ChatStreamEvent::Error {
                message: payload.message,
            }))
        }
        _ => Ok(None),
    }
}

fn parse_event_payload<T>(event_type: &str, data: &str) -> Result<T>
where
    T: DeserializeOwned,
{
    serde_json::from_str(data)
        .wrap_err_with(|| format!("Invalid SSE data for event '{event_type}'"))
}

#[derive(Debug, Deserialize)]
struct ChatCancelResponse {
    cancelled: bool,
}

#[derive(Debug, Deserialize)]
struct PhasePayload {
    phase: String,
}

#[derive(Debug, Deserialize)]
struct DeltaPayload {
    text: String,
}

#[derive(Debug, Deserialize)]
struct ErrorPayload {
    message: String,
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use super::{ChatStream, ChatStreamEvent};

    #[test]
    fn parses_sse_events_and_ignores_comments() {
        let source = concat!(
            ": keep-alive\n\n",
            "event: phase\n",
            "data: {\"phase\":\"thinking\"}\n\n",
            "event: delta\n",
            "data: {\"text\":\"hello\"}\n\n",
            "event: delta\n",
            "data: {\"text\":\" world\"}\n\n",
            "event: done\n",
            "data: {\"thread_id\":\"test\"}\n\n",
        );

        let events = ChatStream::from_reader(Cursor::new(source.as_bytes()))
            .collect::<Result<Vec<_>, _>>()
            .expect("SSE stream should parse");

        assert_eq!(
            events,
            vec![
                ChatStreamEvent::Phase {
                    phase: String::from("thinking"),
                },
                ChatStreamEvent::Delta {
                    text: String::from("hello"),
                },
                ChatStreamEvent::Delta {
                    text: String::from(" world"),
                },
                ChatStreamEvent::Done,
            ]
        );
    }
}
