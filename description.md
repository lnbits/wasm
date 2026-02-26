A safer, permissioned runtime for WASM extensions.

It provides:

- Per-extension KV and secret storage
- Public handlers and public KV reads
- Payment tag watchers and scheduled tasks
- Authenticated handler calls for backend APIs
- Explicit permission grants for internal API access

Designed to let users share and run vibe-coded or unvetted extensions without
modifying LNbits core.
