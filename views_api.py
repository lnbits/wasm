import json
from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from loguru import logger
from starlette.routing import Match

from lnbits.core.crud.extensions import (
    create_user_extension,
    get_installed_extension,
    get_user_extension,
    update_user_extension,
)
from lnbits.core.models.extensions import UserExtension, UserExtensionInfo
from lnbits.decorators import check_admin, check_account_id_exists
from lnbits.settings import settings

from .crud import get_settings, set_settings
from .models import WasmSettings
from .services import load_wasm_settings
from .wasm_host import WASM_HOST_MANIFEST

wasm_api_router = APIRouter()


def _load_extension_config(ext_id: str) -> dict:
    conf_path = Path(settings.lnbits_extensions_path, "extensions", ext_id, "config.json")
    if not conf_path.is_file():
        raise HTTPException(HTTPStatus.NOT_FOUND, f"Extension '{ext_id}' not found.")
    with open(conf_path, "r") as json_file:
        return json.load(json_file)


def _ensure_payment_tags_allowed(required: list[str], granted: list[str]) -> None:
    if not required and granted:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            "This extension does not declare any payment tags.",
        )
    if required and not granted:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            "Select at least one payment tag before enabling this extension.",
        )
    if not required or not granted:
        return
    invalid = [t for t in granted if t not in required]
    if invalid:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            f"Invalid payment tags requested: {', '.join(invalid)}",
        )


def _parse_api_permission(perm: str) -> tuple[str, str] | None:
    if not perm.startswith("api."):
        return None
    try:
        method_part, path = perm.split(":", 1)
        method = method_part.replace("api.", "").upper()
    except ValueError:
        return None
    if not path.startswith("/"):
        return None
    return method, path


def _route_exists(request: Request, method: str, path: str) -> bool:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "root_path": "",
        "headers": [],
    }
    for route in request.app.router.routes:
        methods = getattr(route, "methods", None)
        if methods and method not in methods:
            continue
        try:
            match, _ = route.matches(scope)
        except Exception as exc:
            logger.debug(f"Route match failed for {method} {path}: {exc!s}")
            continue
        if match == Match.FULL:
            return True
    return False


def _missing_api_permissions(request: Request, permissions: list[str]) -> list[str]:
    missing: list[str] = []
    for perm in permissions or []:
        parsed = _parse_api_permission(perm)
        if not parsed:
            continue
        method, path = parsed
        if not _route_exists(request, method, path):
            missing.append(perm)
    return missing


def _ensure_api_permissions_available(request: Request, permissions: list[str]) -> None:
    missing = _missing_api_permissions(request, permissions)
    if missing:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            f"Permissions reference missing endpoints: {', '.join(missing)}",
        )


@wasm_api_router.get("/api/v1/settings", dependencies=[Depends(check_admin)])
async def api_get_settings():
    settings_obj = await get_settings()
    return settings_obj.dict()


@wasm_api_router.put("/api/v1/settings", dependencies=[Depends(check_admin)])
async def api_set_settings(payload: WasmSettings):
    await set_settings(payload)
    await load_wasm_settings()
    return payload.dict()


@wasm_api_router.get("/api/v1/manifest")
async def api_wasm_manifest():
    return WASM_HOST_MANIFEST


@wasm_api_router.get("/api/v1/extensions/{ext_id}/capabilities")
async def api_extension_capabilities(
    ext_id: str,
    request: Request,
    account_id=Depends(check_account_id_exists),
) -> dict:
    config = _load_extension_config(ext_id)
    if config.get("extension_type") != "wasm":
        raise HTTPException(HTTPStatus.NOT_FOUND, "Not a WASM extension")
    permissions_source = config.get("permissions", [])
    permissions = [p.get("id") for p in permissions_source if p.get("id")]
    payment_tags = config.get("payment_tags", [])
    missing = _missing_api_permissions(request, permissions)
    user_ext = await get_user_extension(account_id.id, ext_id)
    granted_permissions = []
    granted_tags = []
    if user_ext and user_ext.extra:
        granted_permissions = user_ext.extra.granted_permissions or []
        granted_tags = user_ext.extra.granted_payment_tags or []
    return {
        "ok": True,
        "extension": ext_id,
        "permissions": permissions_source,
        "missing_permissions": missing,
        "payment_tags": payment_tags,
        "granted_permissions": granted_permissions,
        "granted_payment_tags": granted_tags,
    }


@wasm_api_router.put("/api/v1/extensions/{ext_id}/permissions")
async def api_update_extension_permissions(
    ext_id: str,
    request: Request,
    grant: dict,
    account_id=Depends(check_account_id_exists),
) -> dict:
    config = _load_extension_config(ext_id)
    if config.get("extension_type") != "wasm":
        raise HTTPException(HTTPStatus.NOT_FOUND, "Not a WASM extension")

    ext = await get_installed_extension(ext_id)
    if not ext:
        raise HTTPException(HTTPStatus.NOT_FOUND, f"Extension '{ext_id}' is not installed.")
    if not ext.active:
        raise HTTPException(HTTPStatus.BAD_REQUEST, f"Extension '{ext_id}' is not activated.")

    permissions_source = config.get("permissions", [])
    required_permissions = [p.get("id") for p in permissions_source if p.get("id")]
    granted_permissions = grant.get("permissions") if grant else []
    granted_tags = grant.get("payment_tags") if grant else []
    if not isinstance(granted_permissions, list):
        granted_permissions = []
    if not isinstance(granted_tags, list):
        granted_tags = []

    _ensure_api_permissions_available(request, required_permissions)
    _ensure_payment_tags_allowed(config.get("payment_tags", []), granted_tags)

    if required_permissions:
        missing = [p for p in required_permissions if p not in granted_permissions]
        if missing:
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                "Missing required permissions to save for this extension.",
            )

    user_ext = await get_user_extension(account_id.id, ext_id)
    if not user_ext:
        user_ext = UserExtension(user=account_id.id, extension=ext_id, active=False)
        await create_user_extension(user_ext)

    info = user_ext.extra or UserExtensionInfo()
    info.granted_permissions = granted_permissions
    info.granted_payment_tags = granted_tags
    user_ext.extra = info
    await update_user_extension(user_ext)

    return {"ok": True, "message": f"Permissions saved for '{ext_id}'."}
