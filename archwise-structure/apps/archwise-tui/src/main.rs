use std::io::stdout;

use color_eyre::eyre::Result;
use crossterm::event::{DisableMouseCapture, EnableMouseCapture};
use crossterm::execute;

mod api;
mod app;
mod backend;
mod markdown;
mod ui;

use app::App;
use backend::BackendProcess;

fn main() -> Result<()> {
    color_eyre::install()?;

    let backend = BackendProcess::start()?;
    let mut app = App::new(backend.client())?;
    execute!(stdout(), EnableMouseCapture)?;
    let result = ratatui::run(|terminal| app.run(terminal));
    execute!(stdout(), DisableMouseCapture)?;

    drop(backend);
    result
}
