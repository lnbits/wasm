# WasmExample — Agent Notes (Template)

This extension is a **template** for WASM-only community extensions.
No Python code from the extension is executed by LNbits.

## What This Template Is
- A starting point you copy and change.
- A reference for permissions, proxy usage, and the KV schema.

## What It Can Do (When Permissions Are Granted)
- Read/write the extension KV store (`ext.db.read_write`).
- Call internal LNbits endpoints via the proxy (`api.METHOD:/path`). Check /openapi.json or /docs for available endpoints.
- Register backend payment watchers (`ext.payments.watch`).

## What It Cannot Do
- Access the filesystem.
- Access environment variables or LNbits settings (outside of the API for fetching settings).
- Make outbound network calls.
- Execute Python or shell commands.

## Files You’ll Change
- `config.json`: permissions + `kv_schema`.
- `wasm/`: your WASM module (WAT/Rust/AssemblyScript examples provided).
- `static/` + `templates/`: your UI.

## How to Vibe-Change This Template
1. Update permissions in `config.json` to match the APIs you need.
2. Define KV keys and defaults in `kv_schema`.
3. Replace the UI with your own pages.
4. Build your WASM module and replace `wasm/module.wasm`.

## Limits
- WASM execution is time-limited by `LNBITS_WASM_TIMEOUT_SECONDS`.
- KV writes are validated against `kv_schema` when present.
- Proxy calls are permission-checked (`api.METHOD:/path`).
