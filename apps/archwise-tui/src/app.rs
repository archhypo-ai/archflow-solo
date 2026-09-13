use std::sync::mpsc::{self, Receiver, TryRecvError};
use std::thread;
use std::time::Duration;

use color_eyre::eyre::Result;
use crossterm::event::{self, KeyCode, KeyModifiers};
use ratatui::{DefaultTerminal, Frame};
use uuid::Uuid;

use crate::api::{BackendClient, ChatResponse, ThreadSummary};
use crate::ui;

const LOADING_PHASES: [&str; 3] = ["Connecting", "Thinking", "Answering"];
const LOADING_FRAMES: [&str; 4] = ["|", "/", "-", "\\"];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum Focus {
    Input,
    Conversations,
}

#[derive(Debug)]
pub(crate) enum Confirmation {
    NewConversation,
    DeleteConversation { thread_id: String, title: String },
}

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
    pub(crate) conversations: Vec<ThreadSummary>,
    pub(crate) selected_entry: usize,
    pub(crate) focus: Focus,
    pub(crate) confirmation: Option<Confirmation>,
    pub(crate) pending: Option<Receiver<Result<ChatResponse>>>,
    pub(crate) loading_tick: usize,
    pub(crate) status: String,
    client: BackendClient,
    should_quit: bool,
}

impl App {
    pub fn new(client: BackendClient) -> Result<Self> {
        Ok(Self {
            thread_id: Uuid::new_v4().to_string(),
            input: String::new(),
            character_index: 0,
            messages: Vec::new(),
            conversations: client.list_threads()?,
            selected_entry: 0,
            focus: Focus::Input,
            confirmation: None,
            pending: None,
            loading_tick: 0,
            status: String::from("Ready. Enter sends; Tab switches focus."),
            client,
            should_quit: false,
        })
    }

    pub fn run(&mut self, terminal: &mut DefaultTerminal) -> Result<()> {
        while !self.should_quit {
            self.poll_response();
            self.tick_loading();
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

            if let Some(confirmation) = self.confirmation.take() {
                match (confirmation, key.code) {
                    (
                        Confirmation::NewConversation,
                        KeyCode::Enter | KeyCode::Char('y') | KeyCode::Char('Y'),
                    ) => self.new_conversation(),
                    (
                        Confirmation::DeleteConversation { thread_id, .. },
                        KeyCode::Enter | KeyCode::Char('y') | KeyCode::Char('Y'),
                    ) => self.delete_conversation(&thread_id),
                    (
                        Confirmation::NewConversation | Confirmation::DeleteConversation { .. },
                        KeyCode::Esc | KeyCode::Char('n') | KeyCode::Char('N'),
                    ) => self.status = String::from("Ready."),
                    (confirmation, _) => self.confirmation = Some(confirmation),
                }
                return Ok(());
            }

            if key.code == KeyCode::Esc {
                self.should_quit = true;
                return Ok(());
            }

            if self.is_waiting() {
                return Ok(());
            }

            if key.code == KeyCode::Char('n') && key.modifiers.contains(KeyModifiers::CONTROL) {
                self.request_new_conversation();
                return Ok(());
            }

            if key.code == KeyCode::Tab {
                self.focus = match self.focus {
                    Focus::Input => Focus::Conversations,
                    Focus::Conversations => Focus::Input,
                };
                return Ok(());
            }

            match self.focus {
                Focus::Input => match key.code {
                    KeyCode::Enter => self.submit(),
                    KeyCode::Left => self.move_cursor_left(),
                    KeyCode::Right => self.move_cursor_right(),
                    KeyCode::Backspace => self.delete_char(),
                    KeyCode::Char(character) => self.enter_char(character),
                    _ => {}
                },
                Focus::Conversations => match key.code {
                    KeyCode::Up => self.select_previous_entry(),
                    KeyCode::Down => self.select_next_entry(),
                    KeyCode::Enter => self.activate_selected_entry(),
                    KeyCode::Char('d') | KeyCode::Char('D') => self.request_delete_conversation(),
                    _ => {}
                },
            }
        }

        Ok(())
    }

    fn submit(&mut self) {
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
        self.loading_tick = 0;
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
                self.refresh_conversations();
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

    fn refresh_conversations(&mut self) {
        match self.client.list_threads() {
            Ok(conversations) => {
                self.conversations = conversations;
                self.selected_entry = self
                    .conversations
                    .iter()
                    .position(|conversation| conversation.thread_id == self.thread_id)
                    .map(|index| index + 1)
                    .unwrap_or_else(|| self.selected_entry.min(self.conversations.len()));
            }
            Err(error) => {
                self.status = format!("Conversation list update failed: {error}");
            }
        }
    }

    fn activate_selected_entry(&mut self) {
        if self.selected_entry == 0 {
            self.request_new_conversation();
        } else {
            self.switch_conversation();
        }
    }

    fn switch_conversation(&mut self) {
        let Some(summary) = self.conversations.get(self.selected_entry - 1) else {
            return;
        };
        let thread_id = summary.thread_id.clone();

        match self.client.get_thread(&thread_id) {
            Ok(conversation) => {
                let message_count = conversation.message_count;
                self.thread_id = conversation.thread_id;
                self.messages = conversation
                    .messages
                    .into_iter()
                    .map(|message| UiMessage {
                        role: if message.role == "user" {
                            "You"
                        } else {
                            "ArchWise"
                        },
                        content: message.content,
                    })
                    .collect();
                self.input.clear();
                self.reset_cursor();
                self.focus = Focus::Input;
                self.status = format!("Loaded: {} ({message_count} messages)", conversation.title);
            }
            Err(error) => {
                self.status = format!("Could not load conversation: {error}");
            }
        }
    }

    fn request_new_conversation(&mut self) {
        if self.messages.is_empty() && self.input.is_empty() {
            self.new_conversation();
            return;
        }

        self.confirmation = Some(Confirmation::NewConversation);
        self.status = String::from("Confirm new conversation: Enter/Y confirm, Esc/N cancel.");
    }

    fn new_conversation(&mut self) {
        self.thread_id = Uuid::new_v4().to_string();
        self.messages.clear();
        self.input.clear();
        self.reset_cursor();
        self.selected_entry = 0;
        self.focus = Focus::Input;
        self.confirmation = None;
        self.status = String::from("New conversation.");
    }

    fn request_delete_conversation(&mut self) {
        if self.selected_entry == 0 {
            self.status = String::from("Select a conversation before deleting it.");
            return;
        }

        let Some(conversation) = self.conversations.get(self.selected_entry - 1) else {
            return;
        };
        self.confirmation = Some(Confirmation::DeleteConversation {
            thread_id: conversation.thread_id.clone(),
            title: conversation.title.clone(),
        });
        self.status = String::from("Confirm delete: Enter/Y confirm, Esc/N cancel.");
    }

    fn delete_conversation(&mut self, thread_id: &str) {
        let title = self
            .conversations
            .iter()
            .find(|conversation| conversation.thread_id == thread_id)
            .map(|conversation| conversation.title.clone())
            .unwrap_or_else(|| String::from("conversation"));

        match self.client.delete_thread(thread_id) {
            Ok(()) => {
                if self.thread_id == thread_id {
                    self.thread_id = Uuid::new_v4().to_string();
                    self.messages.clear();
                    self.input.clear();
                    self.reset_cursor();
                    self.selected_entry = 0;
                    self.focus = Focus::Input;
                }
                self.refresh_conversations();
                self.status = format!("Deleted: {title}");
            }
            Err(error) => {
                self.status = format!("Could not delete conversation: {error}");
            }
        }
    }

    fn tick_loading(&mut self) {
        if self.is_waiting() {
            self.loading_tick = self.loading_tick.wrapping_add(1);
        }
    }

    pub(crate) fn loading_status(&self) -> String {
        let phase = LOADING_PHASES[(self.loading_tick / 8) % LOADING_PHASES.len()];
        let frame = LOADING_FRAMES[self.loading_tick % LOADING_FRAMES.len()];
        format!("{phase} {frame}")
    }

    fn select_previous_entry(&mut self) {
        self.selected_entry = self.selected_entry.saturating_sub(1);
    }

    fn select_next_entry(&mut self) {
        self.selected_entry = (self.selected_entry + 1).min(self.conversations.len());
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
