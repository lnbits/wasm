import asyncio

from .crud import get_settings
from .models import WasmSettings

_cached_settings: WasmSettings | None = None
_cache_lock = asyncio.Lock()


async def load_wasm_settings() -> WasmSettings:
    global _cached_settings
    async with _cache_lock:
        _cached_settings = await get_settings()
        return _cached_settings


def get_cached_wasm_settings() -> WasmSettings:
    return _cached_settings or WasmSettings()
