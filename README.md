# WasmExample (WASM-only)

This extension is **WASM-only**: no Python code from the extension is executed.
LNbits runs a trusted **WASM host** that loads and executes the module in a
**separate process**, with explicit permissions.

## Structure

- `config.json` – extension metadata + permissions
- `wasm/module.wat` – the WASM module (compute-only)
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
- `POST /wasmexample/api/v1/invoices/pay`
- `WS /wasmexample/api/v1/events/ws?api_key=<inkey>`

## Websocket updates

Updates are broadcast on channel `wasmexample:<key>`.
The public page connects to `/api/v1/ws/wasmexample:counter`.

## Notes

- The WASM module is executed by `core/wasm/runner.py` using Wasmtime.
- No filesystem or network access is exposed to the module.
- Ensure the Python dependency `wasmtime` is installed in the LNbits environment.
- The module imports host functions `db_get` and `db_set` with a simple string ABI.
