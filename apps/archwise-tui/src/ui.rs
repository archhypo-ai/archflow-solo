use ratatui::layout::{Constraint, Layout, Position, Rect};
use ratatui::style::{Color, Modifier, Style, Stylize};
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::{Block, Clear, List, ListItem, Paragraph, Wrap};
use ratatui::Frame;
use unicode_width::UnicodeWidthStr;

use crate::app::{App, Confirmation, Focus};

pub(crate) fn render(frame: &mut Frame, app: &App) {
    let [conversations_area, chat_area] = frame.area().layout(&Layout::horizontal([
        Constraint::Length(32),
        Constraint::Min(1),
    ]));

    render_conversations(frame, app, conversations_area);
    render_chat(frame, app, chat_area);

    if let Some(confirmation) = app.confirmation.as_ref() {
        render_confirmation(frame, confirmation);
    }
}

fn render_conversations(frame: &mut Frame, app: &App, area: Rect) {
    let mut items = Vec::with_capacity(app.conversations.len() + 1);
    let new_style = if app.focus == Focus::Conversations && app.selected_entry == 0 {
        Style::default().add_modifier(Modifier::REVERSED)
    } else {
        Style::default().fg(Color::Yellow)
    };
    items.push(ListItem::new(Line::from("+ New conversation  (Ctrl+N)")).style(new_style));

    items.extend(
        app.conversations
            .iter()
            .enumerate()
            .map(|(index, conversation)| {
                let marker = if conversation.thread_id == app.thread_id {
                    "* "
                } else {
                    "  "
                };
                let line = Line::from(format!(
                    "{marker}{} ({})",
                    conversation.title, conversation.message_count
                ));
                let style = if app.focus == Focus::Conversations && index + 1 == app.selected_entry
                {
                    Style::default().add_modifier(Modifier::REVERSED)
                } else {
                    Style::default()
                };
                ListItem::new(line).style(style)
            }),
    );

    let title = if app.focus == Focus::Conversations {
        "Conversations [focused]"
    } else {
        "Conversations"
    };
    let list = List::new(items).block(
        Block::bordered()
            .title(title)
            .title_bottom("d delete | Enter open"),
    );
    frame.render_widget(list, area);
}

fn render_chat(frame: &mut Frame, app: &App, area: Rect) {
    let [transcript_area, input_area, status_area] = area.layout(&Layout::vertical([
        Constraint::Min(1),
        Constraint::Length(3),
        Constraint::Length(1),
    ]));

    let transcript = if app.messages.is_empty() {
        Text::from(Line::from("No messages yet.".dark_gray()))
    } else {
        Text::from(
            app.messages
                .iter()
                .flat_map(|message| {
                    [
                        Line::from(Span::styled(
                            format!("{}:", message.role),
                            Style::default().add_modifier(Modifier::BOLD),
                        )),
                        Line::from(message.content.as_str()),
                        Line::from(""),
                    ]
                })
                .collect::<Vec<_>>(),
        )
    };

    frame.render_widget(
        Paragraph::new(transcript)
            .block(Block::bordered().title("Chat"))
            .wrap(Wrap { trim: false }),
        transcript_area,
    );

    frame.render_widget(
        Paragraph::new(app.input.as_str()).block(Block::bordered().title("Message")),
        input_area,
    );

    let focus = match app.focus {
        Focus::Input => "input",
        Focus::Conversations => "conversations",
    };
    let status = if app.is_waiting() {
        app.loading_status()
    } else {
        app.status.clone()
    };
    frame.render_widget(
        Paragraph::new(format!("{status}  Focus: {focus}")).dark_gray(),
        status_area,
    );

    if app.focus == Focus::Input && !app.is_waiting() && app.confirmation.is_none() {
        let prefix = &app.input[..app.cursor_byte_index()];
        let cursor_x = input_area.x + 1 + prefix.width() as u16;
        frame.set_cursor_position(Position::new(cursor_x, input_area.y + 1));
    }
}

fn render_confirmation(frame: &mut Frame, confirmation: &Confirmation) {
    let (title, message, height, accent) = match confirmation {
        Confirmation::NewConversation => (
            " Confirm new conversation ",
            Text::from(vec![
                Line::from("Start a new conversation?"),
                Line::from(""),
                Line::from("Your current conversation will remain saved."),
                Line::from(""),
                Line::from("Enter/Y confirm    Esc/N cancel"),
            ]),
            8,
            Color::Yellow,
        ),
        Confirmation::DeleteConversation { title, .. } => (
            " DELETE CONVERSATION ",
            Text::from(vec![
                Line::from(Span::styled(
                    "PERMANENT ACTION",
                    Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
                )),
                Line::from(""),
                Line::from(format!("Conversation: \"{title}\"")),
                Line::from(""),
                Line::from("All messages and checkpoint data will be removed."),
                Line::from("This action cannot be undone."),
                Line::from(""),
                Line::from("Enter/Y delete    Esc/N cancel"),
            ]),
            11,
            Color::Red,
        ),
    };
    let border_style = Style::default().fg(accent);
    let area = centered_rect(frame.area(), 76, height);
    frame.render_widget(Clear, area);
    frame.render_widget(
        Paragraph::new(message)
            .alignment(ratatui::layout::Alignment::Center)
            .wrap(Wrap { trim: false })
            .block(
                Block::bordered()
                    .title(title)
                    .title_style(border_style.add_modifier(Modifier::BOLD))
                    .border_style(border_style),
            ),
        area,
    );
}

fn centered_rect(area: Rect, width: u16, height: u16) -> Rect {
    let width = width.min(area.width.saturating_sub(2));
    let height = height.min(area.height.saturating_sub(2));
    Rect::new(
        area.x + area.width.saturating_sub(width) / 2,
        area.y + area.height.saturating_sub(height) / 2,
        width,
        height,
    )
}
