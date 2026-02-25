from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_admin
from lnbits.helpers import template_renderer

wasm_router = APIRouter()


@wasm_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_admin)):
    return template_renderer(["wasm/templates"]).TemplateResponse(
        "wasm/index.html", {"request": request, "user": user}
    )
