use ratatui::layout::{Constraint, Layout};
use ratatui::style::{Modifier, Style, Stylize};
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::{Block, Paragraph, Wrap};
use ratatui::{layout::Position, Frame};
use unicode_width::UnicodeWidthStr;

use crate::app::App;

pub(crate) fn render(frame: &mut Frame, app: &App) {
    let [transcript_area, input_area, status_area] = frame.area().layout(&Layout::vertical([
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
            .block(Block::bordered().title("ArchWise"))
            .wrap(Wrap { trim: false }),
        transcript_area,
    );

    frame.render_widget(
        Paragraph::new(app.input.as_str())
            .block(Block::bordered().title("Message"))
            .wrap(Wrap { trim: false }),
        input_area,
    );

    frame.render_widget(
        Paragraph::new(format!("{}  Thread: {}", app.status, app.thread_id)).dark_gray(),
        status_area,
    );

    if !app.is_waiting() {
        let prefix = &app.input[..app.cursor_byte_index()];
        let cursor_x = input_area.x + 1 + prefix.width() as u16;
        frame.set_cursor_position(Position::new(cursor_x, input_area.y + 1));
    }
}
