---
layout: default
parent: For developers
title: Agent Guide - WASM Extensions
nav_order: 3
---

# Agent Guide - WASM Extensions

This guide is written for AI agents or developers using AI to build LNbits WASM extensions. It describes what to change, what not to change, and the available capabilities/limits.

## Hard Rules (Non-Negotiable)

- Do **not** change core LNbits files. Only edit files inside your extension folder.
- Do **not** add new Python dependencies.
- Do **not** rely on long-running WASM processes. WASM runs per-call with timeouts.

## Extension Folder Layout (WASM)

Your extension lives under:

```
lnbits/extensions/<ext_id>/
```

You should only edit files under this folder, typically:

- `config.json` (metadata, permissions, tags, public handlers)
- `wasm/` (your `module.wasm` or `module.wat`)
- `static/` (frontend assets)
- `templates/` (HTML pages)
- `manifest.json`, `README.md`, `description.md` (docs and metadata)

## Required Config Fields

In `config.json`:

- `id` / `name`
- `extension_type: "wasm"`
- `permissions` (required API permissions)
- `public_wasm_functions` (handlers callable from public routes)
- `public_kv_keys` (publicly readable KV keys)
- `payment_tags` (list of tags the user may grant for watcher access)

Example:

```json
{
  "id": "myext",
  "name": "MyExt",
  "extension_type": "wasm",
  "permissions": [
    {"id": "ext.db.read_write", "label": "DB access", "description": "..."},
    {
      "id": "api.POST:/api/v1/payments",
      "label": "Create invoices",
      "description": "..."
    },
    {
      "id": "ext.payments.watch",
      "label": "Watch payments",
      "description": "..."
    },
    {
      "id": "ext.tasks.schedule",
      "label": "Schedule tasks",
      "description": "..."
    },
    {"id": "ext.db.sql", "label": "SQL access", "description": "..."}
  ],
  "public_wasm_functions": [
    "public_create_invoice",
    "on_tag_payment",
    "on_schedule"
  ],
  "public_kv_keys": ["public_lists", "public_tasks"],
  "payment_tags": ["coinflip", "myext"]
}
```

## What the WASM Host Can Do

WASM runs in a short-lived subprocess. It can:

- Read/write extension KV (`/api/v1/kv/*`)
- Read/write secret KV (`/api/v1/secret/*`)
- Call internal LNbits endpoints (only if declared + granted)
- Publish websockets (`ws_publish`)
- Run backend tag watchers and scheduled handlers (server-side triggers)

## Permissions Model

Your extension can only call or access what is declared and granted:

- `api.METHOD:/path` for internal endpoints (core or other extensions)
- `ext.db.read_write` for KV access
- `ext.payments.watch` for payment watchers
- `ext.tasks.schedule` for scheduled jobs
- `ext.db.sql` for SQL interface

If the endpoint doesn’t exist, permissions won’t save.

**Payments rule (read this if you touch `/api/v1/payments`)**

For `POST /api/v1/payments`, the WASM bridge enforces:

- You **must** include `"out": true|false` explicitly in the request body.
- You **must** declare a policy in `config.json`, and the bridge **enforces it**.

Use this in your permission to make intent explicit and safe:

```json
{
  "id": "api.POST:/api/v1/payments",
  "label": "Create invoices",
  "description": "Create invoices only.",
  "policy": {"payments_out": false}
}
```

If you need to **pay** invoices, set `"policy": {"payments_out": true}` and send `"out": true` in your request body.

## Tag Watchers (Backend)

You can register tag watchers:

```
POST /<ext_id>/api/v1/watch_tag
{
  "tag": "coinflip",
  "wallet_id": "<wallet-id>",
  "handler": "on_tag_payment",
  "store_key": "tag:coinflip:last_payment"
}
```

Constraints:

- Tag must be in `payment_tags` and granted by the user.
- Watchers are persisted and restored on restart.

## Scheduled Tasks (Backend)

You can schedule periodic handlers:

```
POST /<ext_id>/api/v1/schedule
{
  "interval_seconds": 30,
  "handler": "on_schedule",
  "store_key": "schedule:last_run"
}
```

Constraints:

- Requires `ext.tasks.schedule` permission.
- Minimum interval is 5 seconds.
- Stored in extension KV and restored on restart.

## SQL Interface (Limited)

You can run SQL within your extension schema:

- `/api/v1/sql/query` (SELECT only)
- `/api/v1/sql/exec` (limited DDL/DML)

Rules:

- Single statement only
- No `PRAGMA`, no `sqlite_master`
- No cross-schema access

## Public Pages (No Keys)

Public pages must not depend on `window.g` or wallet keys.
They can call:

- `/{ext_id}/api/v1/public/kv/{key}`
- `/{ext_id}/api/v1/public/call/{handler}`

## Authenticated Handler Calls (Backend API)

For authenticated users, the WASM host exposes:

```
POST /{ext_id}/api/v1/call/{handler}
```

Requirements:

- User must have the extension enabled.
- Requires `ext.db.read_write` permission.

Behavior:

- Stores payload in `request` / `request:{id}` (and mirrors to `public_request` keys).
- Executes the handler with the request id.
- Returns the handler response from `response` / `public_response`.
- Supports `watch` + `list_updates` the same way public calls do.

## Quick Start (Minimal Extension)

1. Create `lnbits/extensions/<ext_id>/config.json` with `extension_type: "wasm"` and required permissions.
2. Add `wasm/module.wasm` (or `module.wat`) exporting at least one handler.
3. Create `templates/<ext_id>/index.html` and `static/js/index.js`.
4. Store UI state in `tasks` or `lists` KV keys and mirror to `public_*` keys for public pages.

## Canonical Paid Flow (Create → Watch → Update Record → WS)

Backend or public page calls a handler that creates an invoice:

```
POST /{ext_id}/api/v1/call/public_create_invoice
{
  "raw": "<task_id>",
  "watch": {
    "store_key": "task_event:last_payment",
    "tag": "myext",
    "handler": "noop",
    "list_updates": [
      {"key": "tasks", "id": "<task_id>", "field": "paid", "value": true},
      {"key": "public_tasks", "id": "<task_id>", "field": "paid", "value": true}
    ]
  }
}
```

What happens:

1. The handler creates an invoice via `http_request` to `/api/v1/payments`.
2. The host registers a payment watch and stores the invoice response.
3. When paid, the host updates the task record and emits websocket updates.

## Recommended Data Model

- Store full records in `tasks` (private) and mirror into `public_tasks` (public).
- Each task record should include `id`, `list_id`, `title`, `cost_sats`, `paid`.
- Avoid separate `task_paid:<id>` keys; keep `paid` in the record.

## Safe Defaults (Permissions)

- Always require `ext.db.read_write`.
- Add `api.POST:/api/v1/payments` only if you create invoices.
- Add `ext.payments.watch` only if you use `watch` or `watch_tag`.
- Keep public handlers minimal and avoid privileged operations.

## What Not To Do

- Do not write to core routes or override existing LNbits paths.
- Do not add background threads; use watchers or scheduler instead.
- Do not assume the WASM process persists.

## Testing Checklist

- Permissions show correctly in the extensions UI.
- Public handlers are in `public_wasm_functions`.
- Public KV keys are explicitly listed.
- Tag watchers only use allowed tags.
- Scheduled handlers run and update KV as expected.
