# WasmExample (WASM-only)

A minimal extension demonstrating a **WASM-only** execution model:

- No Python code from the extension is executed.
- The WASM module runs in a **separate process** using Wasmtime.
- Permissions are explicitly granted when enabling the extension.
- Public page updates live via websocket.
