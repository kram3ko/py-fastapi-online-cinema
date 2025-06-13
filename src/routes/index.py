from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    base_url = request.base_url
    hostname = request.url.hostname
    scheme = request.url.scheme

    def custom_url(port: int, path: str) -> str:
        if hostname in {"127.0.0.1", "localhost"}:
            return f"{scheme}://{hostname}:{port}/"
        return f"{base_url}{path}"

    docs_url = f"{base_url}docs"
    pgadmin_url = custom_url(3333, "pgadmin")
    flower_url = custom_url(5540, "flower")
    mailhog_url = custom_url(8025, "mailhog")
    redisinsight_url = f"{scheme}://{hostname}:5540"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "member1": "Volodya Vinohradov",
        "member2": "Krystya las_name",
        "member3": "Bronn last_name",
        "member4": "Happy last_name",
        "member5": "Lebron last_name",
        "pgadmin_url": pgadmin_url,
        "flower": flower_url,
        "docs_url": docs_url,
        "mailhog_url": mailhog_url,
        "redisinsight_url": redisinsight_url,
    })
