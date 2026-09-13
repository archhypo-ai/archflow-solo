# archwise-tui

Minimal Ratatui client for the local ArchWise backend.

## Run

Start the Python backend first:

```bash
cd libs/archwise-agent
uv run fastapi dev --host 127.0.0.1 --port 8765
```

Then, from the repository root, start the TUI:

```bash
cargo run --manifest-path apps/archwise-tui/Cargo.toml
```

Type a message and press `Enter`. Use arrow keys to move the cursor. Press
`Esc` or `Ctrl+C` to exit.

The TUI uses Ratatui widgets (`Block`, `Paragraph`, and `Wrap`) and keeps
application state, HTTP communication, and rendering in separate modules:

```text
src/
├── main.rs
├── app.rs
├── api.rs
└── ui.rs
```

The TUI currently connects to `http://127.0.0.1:8765` and does not start the
backend process itself. Backend process management will be added after this
basic communication path is validated.
