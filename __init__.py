import asyncio

from fastapi import APIRouter
from loguru import logger

from .crud import db
from .views import wasm_router
from .views_api import wasm_api_router
from .wasm_host.extension_host import handle_wasm_tag_payment, wasm_scheduler


wasm_ext = APIRouter(prefix="/wasm", tags=["WASM"])
wasm_ext.include_router(wasm_router)
wasm_ext.include_router(wasm_api_router)

wasm_static_files = [
    {
        "path": "/wasm/static",
        "name": "wasm_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def wasm_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def wasm_start():
    from lnbits.tasks import (
        create_permanent_unique_task,
        create_task,
        wait_for_paid_invoices,
    )
    from .services import load_wasm_settings

    async def _init_settings():
        await load_wasm_settings()

    create_task(_init_settings())
    task = create_permanent_unique_task(
        "ext_wasm_tags", wait_for_paid_invoices("wasm_tags", handle_wasm_tag_payment)
    )
    scheduled_tasks.append(task)
    task = create_permanent_unique_task("ext_wasm_scheduler", wasm_scheduler)
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "wasm_ext",
    "wasm_start",
    "wasm_static_files",
    "wasm_stop",
]
