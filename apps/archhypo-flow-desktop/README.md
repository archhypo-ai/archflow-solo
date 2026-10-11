# ArchHypo Flow Desktop

Tauri and React desktop chat harness using the latest `@assistant-ui/react` package. The interface supports English and Brazilian Portuguese, detects the system language on first launch, and remembers the selected language. Tokyo Night and Tokyo Day color tokens are centralized in `src/theme/tokens.css`, using the palette from [Ashtrath's Tokyo Night theme](https://github.com/ashtrath/Tokyo-Night/tree/main/themes). The account menu provides a language submenu and a Settings dialog. Its General section shows the app version and lets users choose appearance and language. On Linux, the Tauri entry point disables WebKitGTK's DMA-BUF renderer by default to avoid blank windows on affected graphics drivers; an explicitly set `WEBKIT_DISABLE_DMABUF_RENDERER` value is preserved.

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
