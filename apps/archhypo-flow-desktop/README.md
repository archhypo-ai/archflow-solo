# ArchHypo Flow Desktop

Tauri and React desktop chat harness using the latest `@assistant-ui/react` package. Tokyo Night and Tokyo Night Day color tokens are centralized in `src/theme/tokens.css`; the sidebar theme control switches between them. On Linux, the Tauri entry point disables WebKitGTK's DMA-BUF renderer by default to avoid blank windows on affected graphics drivers; an explicitly set `WEBKIT_DISABLE_DMABUF_RENDERER` value is preserved.

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
