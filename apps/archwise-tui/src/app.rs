use std::sync::mpsc::{self, Receiver, TryRecvError};
use std::thread;
use std::time::Duration;

use color_eyre::eyre::Result;
use crossterm::event::{self, KeyCode, KeyModifiers};
use ratatui::{DefaultTerminal, Frame};
use uuid::Uuid;

use crate::api::{BackendClient, ChatResponse};
use crate::ui;

#[derive(Debug)]
pub(crate) struct UiMessage {
    pub(crate) role: &'static str,
    pub(crate) content: String,
}

pub struct App {
    pub(crate) thread_id: String,
    pub(crate) input: String,
    pub(crate) character_index: usize,
    pub(crate) messages: Vec<UiMessage>,
    pub(crate) pending: Option<Receiver<Result<ChatResponse>>>,
    pub(crate) status: String,
    client: BackendClient,
    should_quit: bool,
}

impl App {
    pub fn new(client: BackendClient) -> Self {
        Self {
            thread_id: Uuid::new_v4().to_string(),
            input: String::new(),
            character_index: 0,
            messages: Vec::new(),
            pending: None,
            status: String::from("Ready. Enter sends; Esc exits."),
            client,
            should_quit: false,
        }
    }

    pub fn run(&mut self, terminal: &mut DefaultTerminal) -> Result<()> {
        while !self.should_quit {
            self.poll_response();
            terminal.draw(|frame| self.render(frame))?;
            self.handle_events()?;
        }
        Ok(())
    }

    fn render(&self, frame: &mut Frame) {
        ui::render(frame, self);
    }

    fn handle_events(&mut self) -> Result<()> {
        if !event::poll(Duration::from_millis(100))? {
            return Ok(());
        }

        if let Some(key) = event::read()?.as_key_press_event() {
            if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) {
                self.should_quit = true;
                return Ok(());
            }

            match key.code {
                KeyCode::Esc => self.should_quit = true,
                KeyCode::Enter => self.submit(),
                KeyCode::Left if !self.is_waiting() => self.move_cursor_left(),
                KeyCode::Right if !self.is_waiting() => self.move_cursor_right(),
                KeyCode::Backspace if !self.is_waiting() => self.delete_char(),
                KeyCode::Char(character) if !self.is_waiting() => {
                    self.enter_char(character);
                }
                _ => {}
            }
        }

        Ok(())
    }

    fn submit(&mut self) {
        if self.is_waiting() {
            return;
        }

        let message = self.input.trim().to_owned();
        if message.is_empty() {
            self.status = String::from("Message cannot be empty.");
            return;
        }

        self.input.clear();
        self.reset_cursor();
        self.messages.push(UiMessage {
            role: "You",
            content: message.clone(),
        });
        self.status = String::from("Waiting for backend...");

        let client = self.client.clone();
        let thread_id = self.thread_id.clone();
        let (sender, receiver) = mpsc::channel();
        self.pending = Some(receiver);

        thread::spawn(move || {
            let result = client.send_message(&thread_id, &message);
            let _ = sender.send(result);
        });
    }

    fn poll_response(&mut self) {
        let result = match self.pending.as_ref() {
            None => return,
            Some(receiver) => match receiver.try_recv() {
                Ok(result) => result,
                Err(TryRecvError::Empty) => return,
                Err(TryRecvError::Disconnected) => Err(color_eyre::eyre::eyre!(
                    "Backend request channel disconnected."
                )),
            },
        };

        self.pending = None;
        match result {
            Ok(response) => {
                self.messages.push(UiMessage {
                    role: "ArchWise",
                    content: response.message,
                });
                self.status = String::from("Ready.");
            }
            Err(error) => {
                self.messages.push(UiMessage {
                    role: "Error",
                    content: error.to_string(),
                });
                self.status = String::from("Request failed.");
            }
        }
    }

    pub(crate) fn is_waiting(&self) -> bool {
        self.pending.is_some()
    }

    fn enter_char(&mut self, character: char) {
        let index = self.byte_index();
        self.input.insert(index, character);
        self.move_cursor_right();
    }

    fn move_cursor_left(&mut self) {
        self.character_index = self.character_index.saturating_sub(1);
    }

    fn move_cursor_right(&mut self) {
        self.character_index = (self.character_index + 1).min(self.input.chars().count());
    }

    fn delete_char(&mut self) {
        if self.character_index == 0 {
            return;
        }

        let current_index = self.character_index;
        let before = self.input.chars().take(current_index - 1);
        let after = self.input.chars().skip(current_index);
        self.input = before.chain(after).collect();
        self.move_cursor_left();
    }

    fn byte_index(&self) -> usize {
        self.input
            .char_indices()
            .map(|(index, _)| index)
            .nth(self.character_index)
            .unwrap_or(self.input.len())
    }

    fn reset_cursor(&mut self) {
        self.character_index = 0;
    }

    pub(crate) fn cursor_byte_index(&self) -> usize {
        self.byte_index()
    }
}
