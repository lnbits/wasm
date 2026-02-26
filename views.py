from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists

from .helpers import wasm_renderer

wasm_router = APIRouter()


@wasm_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    if not user.admin:
        raise HTTPException(
            HTTPStatus.FORBIDDEN, "User not authorized. No admin privileges."
        )
    return wasm_renderer().TemplateResponse(
        "wasm/index.html", {"request": request, "user": user.json()}
    )
