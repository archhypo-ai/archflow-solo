use std::fmt::{Display, Formatter};
use std::io::BufRead;
use std::sync::atomic::{AtomicBool, Ordering};

use super::models::AgentEvent;

#[derive(Debug)]
pub enum StreamError {
    Io(std::io::Error),
    Json(serde_json::Error),
}

impl Display for StreamError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(error) => write!(formatter, "SSE read failed: {error}"),
            Self::Json(error) => write!(formatter, "Invalid agent stream JSON: {error}"),
        }
    }
}

impl std::error::Error for StreamError {}

impl From<std::io::Error> for StreamError {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}

impl From<serde_json::Error> for StreamError {
    fn from(error: serde_json::Error) -> Self {
        Self::Json(error)
    }
}

pub struct SseDecoder<R> {
    reader: R,
    event_type: Option<String>,
    data_lines: Vec<String>,
}

impl<R: BufRead> SseDecoder<R> {
    pub fn from_reader(reader: R) -> Self {
        Self {
            reader,
            event_type: None,
            data_lines: Vec::new(),
        }
    }

    pub fn next_with_cancellation(
        &mut self,
        cancellation: &AtomicBool,
    ) -> Option<Result<AgentEvent, StreamError>> {
        self.next_event(Some(cancellation))
    }

    fn next_event(
        &mut self,
        cancellation: Option<&AtomicBool>,
    ) -> Option<Result<AgentEvent, StreamError>> {
        loop {
            if cancellation.is_some_and(|token| token.load(Ordering::Relaxed)) {
                return None;
            }

            let mut line = String::new();
            match self.reader.read_line(&mut line) {
                Ok(0) => return self.dispatch_pending(),
                Ok(_) => {}
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

    fn dispatch_pending(&mut self) -> Option<Result<AgentEvent, StreamError>> {
        self.event_type.take();
        let data = std::mem::take(&mut self.data_lines).join("\n");
        if data.is_empty() {
            return None;
        }
        Some(serde_json::from_str(&data).map_err(StreamError::from))
    }
}

impl<R: BufRead> Iterator for SseDecoder<R> {
    type Item = Result<AgentEvent, StreamError>;

    fn next(&mut self) -> Option<Self::Item> {
        self.next_event(None)
    }
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use super::SseDecoder;
    use crate::AgentEvent;

    #[test]
    fn decodes_agent_events_from_sse() {
        let source = concat!(
            ": keep-alive\n\n",
            "event: archwise\n",
            "data: {\"protocol_version\":1,\"run_id\":\"r\",\"thread_id\":\"t\",\"type\":\"text_delta\",\"text\":\"hi\"}\n\n",
            "event: archwise\n",
            "data: {\"protocol_version\":1,\"run_id\":\"r\",\"thread_id\":\"t\",\"type\":\"done\",\"status\":\"completed\"}\n\n",
        );

        let events = SseDecoder::from_reader(Cursor::new(source.as_bytes()))
            .collect::<Result<Vec<_>, _>>()
            .expect("SSE should decode");

        assert!(matches!(events[0], AgentEvent::TextDelta { .. }));
        assert!(matches!(events[1], AgentEvent::Done { .. }));
    }
}
