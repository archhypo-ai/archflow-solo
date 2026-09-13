use color_eyre::eyre::Result;

mod api;
mod app;
mod ui;

use api::{BackendClient, DEFAULT_BACKEND_URL};
use app::App;

fn main() -> Result<()> {
    color_eyre::install()?;
    let client = BackendClient::new(DEFAULT_BACKEND_URL)?;
    let mut app = App::new(client);

    ratatui::run(|terminal| app.run(terminal))
}
