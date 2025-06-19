from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    hostname = request.url.hostname
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    base_url = request.base_url

    def correct_url(port: int, prefix: str) -> str:
        if hostname in {"127.0.0.1", "localhost"}:
            return f"{scheme}://{hostname}:{port}/"
        return f"{base_url}{prefix}"

    docs_url = f"{base_url}docs"
    pgadmin_url = correct_url(3333, "pgadmin")
    flower_url = correct_url(5555, "flower")
    mailhog_url = correct_url(8025, "mailhog")
    redisinsight_url = f"{scheme}://{hostname}:{5540}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "pgadmin_url": pgadmin_url,
        "flower": flower_url,
        "docs_url": docs_url,
        "mailhog_url": mailhog_url,
        "redisinsight_url": redisinsight_url,
    })
