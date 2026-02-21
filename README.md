# WasmExample (WASM-only)

This extension is **WASM-only**: no Python code from the extension is executed.
LNbits runs a trusted **WASM host** that loads and executes the module in a
**separate process**, with explicit permissions.

## Structure

- `config.json` – extension metadata + permissions
- `wasm/module.wat` – the WASM module (compute-only)
- `wasm/rust-example/` – minimal Rust source that compiles to WASM
- `templates/wasmexample/` – index + public pages
- `static/` – JS and assets

## Permissions (declared in `config.json`)

- `ext.db.read_write` – Access extension database
- `lnbits.invoice.create` – Create invoices from a selected wallet
- `lnbits.invoice.pay` – Pay invoices from a selected wallet

LNbits shows a dialog when enabling the extension and requires explicit consent.

## API (provided by the core WASM host)

- `GET /wasmexample/api/v1/kv/{key}`
- `POST /wasmexample/api/v1/kv/{key}`
- `POST /wasmexample/api/v1/kv/{key}/increment` (uses WASM)
- `GET /wasmexample/api/v1/public/kv/{key}`
- `POST /wasmexample/api/v1/invoices`
- `POST /wasmexample/api/v1/invoices/increment` (creates invoice + backend increment)
- `POST /wasmexample/api/v1/invoices/pay`
- `WS /wasmexample/api/v1/events/ws?api_key=<inkey>`
- `POST /wasmexample/api/v1/proxy` (permissioned internal API proxy)

## Websocket updates

Updates are broadcast on channel `wasmexample:<key>`.
The public page connects to `/api/v1/ws/wasmexample:counter`.

## Invoice flow example

The main page demonstrates a common extension pattern:

- User clicks "Create Invoice to Increment".
- The extension creates a Lightning invoice (permissioned).
- The UI shows a QR and listens for payment over websocket.
- When paid, the backend calls WASM to increment and broadcasts the update.

The invoice amount is read by WASM from the extension DB key
`increment_amount` (defaults to `10`). The UI writes this key before creating
the invoice.

## Internal API proxy

WASM extensions cannot access the network. If you need to call core or extension
endpoints, use the permissioned proxy:

```json
{
  "method": "POST",
  "path": "/api/v1/payments",
  "body": {"out": false, "amount": 10, "memo": "Example"}
}
```

Permission format: `api.METHOD:/path` (exact match).

## Notes

- The WASM module is executed by `core/wasm/runner.py` using Wasmtime.
- No filesystem or network access is exposed to the module.
- Ensure the Python dependency `wasmtime` is installed in the LNbits environment.
- The module imports host functions `db_get` and `db_set` with a simple string ABI.

## Rust example (build to `module.wasm`)

Source lives in `wasm/rust-example/`. It mirrors the behavior of `module.wat`
and exports `increment_counter` and `get_increment_amount`.

Build steps:

```bash
cd extensions/wasmexample/wasm/rust-example
rustup target add wasm32-unknown-unknown
cargo build --release --target wasm32-unknown-unknown
cp target/wasm32-unknown-unknown/release/wasmexample.wasm ../module.wasm
```
