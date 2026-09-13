# ArchWISE Desktop

Tauri 2 desktop shell for ArchWISE.

## Current scope

This first increment is visual only. It includes a React/Vite shell, a collapsible sidebar, local conversation navigation, theme tokens, and an assistant-ui thread/composer runtime that stores messages locally. It does not start the Python backend or communicate with the agent.

The local runtime is deliberately isolated in `src/features/chat/hooks/useLocalChatRuntime.ts`. It can later be replaced by the agent runtime without changing the shell components.

## Development

```bash
npm install
npm run dev          # Browser preview
npm run tauri:dev    # Tauri desktop window
```

## Architecture rule

Components render UI and emit events. Hooks own state and behavior. Agent/API integration will be added behind feature hooks and clients in a later increment; components should not import transport code directly.
