use ratatui::style::Style;
use ratatui::text::{Line, Span, Text};
use unicode_width::UnicodeWidthStr;

/// Convert assistant Markdown into wrapped Ratatui-styled text.
pub(crate) fn render(content: &str, width: u16) -> Text<'static> {
    let markdown = tui_markdown::from_str(content);
    let width = usize::from(width.max(1));
    let lines: Vec<Line<'static>> = markdown
        .lines
        .iter()
        .flat_map(|line| wrap_line(line, width))
        .collect();
    Text::from(lines)
}

fn wrap_line(line: &Line<'_>, width: usize) -> Vec<Line<'static>> {
    if line.spans.is_empty() {
        return vec![Line::from("")];
    }

    let mut lines = Vec::new();
    let mut spans = Vec::new();
    let mut span_text = String::new();
    let mut span_style = None;
    let mut column = 0;

    for grapheme in line.styled_graphemes(line.style) {
        let grapheme_width = grapheme.symbol.width();
        if grapheme_width > 0 && column > 0 && column + grapheme_width > width {
            push_span(&mut spans, &mut span_text, &mut span_style);
            lines.push(Line::from(std::mem::take(&mut spans)));
            column = 0;
        }

        if span_style != Some(grapheme.style) && !span_text.is_empty() {
            push_span(&mut spans, &mut span_text, &mut span_style);
        }
        if span_style.is_none() {
            span_style = Some(grapheme.style);
        }
        span_text.push_str(grapheme.symbol);
        column = column.saturating_add(grapheme_width);
    }

    push_span(&mut spans, &mut span_text, &mut span_style);
    if spans.is_empty() {
        lines.push(Line::from(""));
    } else {
        lines.push(Line::from(spans));
    }
    lines
}

fn push_span(spans: &mut Vec<Span<'static>>, text: &mut String, style: &mut Option<Style>) {
    if text.is_empty() {
        return;
    }
    spans.push(Span::styled(
        std::mem::take(text),
        style.take().unwrap_or_default(),
    ));
}
