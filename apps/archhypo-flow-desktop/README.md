# ArchHypo Flow Desktop

Tauri and React desktop chat harness using the latest `@assistant-ui/react` package. The interface supports English and Brazilian Portuguese, detects the system language on first launch, and remembers the selected language. Appearance can follow the system preference or be fixed to Day or Night, using Tokyo palette tokens centralized in `src/theme/tokens.css`. The account menu provides a language submenu and a Settings dialog. The sidebar can create and list local projects; project names, icons, colors, and additional instructions are stored locally. The current demo chat does not yet apply project instructions to an agent. On Linux, the Tauri entry point disables WebKitGTK's DMA-BUF renderer by default to avoid blank windows on affected graphics drivers; an explicitly set `WEBKIT_DISABLE_DMABUF_RENDERER` value is preserved.

The current chat runtime returns local demonstration responses. It does not call the LangGraph agent or persist conversations yet.

## Development

```bash
npm install
npm run tauri dev
```

Build the frontend with:

```bash
npm run build
```
