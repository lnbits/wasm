# WasmExample (Template)

This is a **template** WASM extension meant to be copied and modified.
No Python code from the extension is executed. The host only exposes the
explicit permissions you declare in `config.json`.

## What You Change First

- Update `config.json` permissions to the APIs you need.
- Update `kv_schema` for the keys your extension will store.
- Replace the UI in `templates/` and `static/`.
- Replace the WASM module in `wasm/`.

## What It Cannot Do
- Access the filesystem.
- Access environment variables or LNbits settings.
- Make outbound network calls.
- Execute Python or shell commands.

## Permissions (Summary)

- `ext.db.read_write` controls access to the extension KV store.
- `api.METHOD:/path` lets the extension call internal LNbits endpoints through
  the proxy (exact path match).
- `ext.payments.watch` lets the extension register backend payment watchers.

Permissions are shown at enable time and must be explicitly approved.

## Internal API Proxy

WASM extensions can call **any internal LNbits endpoint** by declaring
the matching permission and using:

`POST /{ext_id}/api/v1/proxy`

Example:

```json
{
  "method": "POST",
  "path": "/api/v1/payments",
  "body": {"out": false, "amount": 10, "memo": "Example"}
}
```

## Build WASM

You can compile in any language that targets WASM. This template includes:

- `wasm/module.wat` (minimal WAT)
- `wasm/rust-example/` (Rust)
- `wasm/assemblyscript-example/` (AssemblyScript)

Each example folder includes build instructions.
