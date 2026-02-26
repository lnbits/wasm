import json

from lnbits.db import Database

from .models import WasmSettings

db = Database("ext_wasm")


async def _ensure_settings_table() -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS wasm.settings (
            id TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )


async def get_settings() -> WasmSettings:
    await _ensure_settings_table()
    row = await db.fetchone(
        "SELECT value FROM wasm.settings WHERE id = :id",
        {"id": "global"},
    )
    if not row or not row.get("value"):
        return WasmSettings()
    try:
        data = json.loads(row["value"])
    except Exception:
        return WasmSettings()
    return WasmSettings(**data)


async def set_settings(settings: WasmSettings) -> None:
    await _ensure_settings_table()
    value = settings.dict()
    payload = json.dumps(value)
    existing = await db.fetchone(
        "SELECT id FROM wasm.settings WHERE id = :id",
        {"id": "global"},
    )
    if existing:
        await db.execute(
            "UPDATE wasm.settings SET value = :value WHERE id = :id",
            {"id": "global", "value": payload},
        )
    else:
        await db.execute(
            "INSERT INTO wasm.settings (id, value) VALUES (:id, :value)",
            {"id": "global", "value": payload},
        )
