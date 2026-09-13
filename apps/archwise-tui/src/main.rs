use color_eyre::eyre::Result;

mod api;
mod app;
mod backend;
mod ui;

use app::App;
use backend::BackendProcess;

fn main() -> Result<()> {
    color_eyre::install()?;

    let backend = BackendProcess::start()?;
    let mut app = App::new(backend.client())?;
    let result = ratatui::run(|terminal| app.run(terminal));

    drop(backend);
    result
}
