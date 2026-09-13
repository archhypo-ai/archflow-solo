# ArchWISE Desktop

Tauri 2 desktop shell for ArchWISE.

## Current scope

The shell includes a collapsible sidebar, local conversation navigation, an Anonymous account menu, Settings (General and Agent), theme tokens, and an assistant-ui thread/composer runtime.

The development process starts the Python backend with `scripts/start-backend.mjs`; the Tauri layer remains a native window shell. The React webview communicates with the backend over its HTTP API. The chat currently uses request/response HTTP; streaming and SSE will be introduced when the backend exposes a streaming contract.

The agent runtime is isolated in `src/features/chat/hooks/useAgentChatRuntime.ts`, and HTTP transport is isolated in `src/features/agent/api/agentClient.ts`. Shell components do not import transport code.

## Development

```bash
npm install
npm run dev:all      # Browser preview + Python backend
npm run tauri:dev    # Tauri desktop window + Python backend
```

## Architecture rule

Components render UI and emit events. Hooks own state and behavior. Agent/API integration will be added behind feature hooks and clients in a later increment; components should not import transport code directly.
