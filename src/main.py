from fastapi import FastAPI, Request
from fastapi_pagination import add_pagination
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from routes.accounts import router as accounts_router
from routes.movies import router as movie_router
from routes.orders import router as orders_router
from routes.payments import router as payments_router
from routes.profiles import router as profiles_router
from routes.shopping_cart import router as cart_router

app = FastAPI(title="Online Cinema", description="Group project Online Cinema API")

api_version_prefix = "/api/v1"

app.include_router(accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"])
app.include_router(profiles_router, prefix=f"{api_version_prefix}/profiles", tags=["profiles"])
app.include_router(movie_router, prefix=f"{api_version_prefix}/online_cinema", tags=["movies"])

app.include_router(payments_router, prefix=f"{api_version_prefix}/payments", tags=["payments"])
app.include_router(cart_router, prefix=f"{api_version_prefix}/cart", tags=["cart"])
app.include_router(orders_router, prefix=f"{api_version_prefix}/orders", tags=["orders"])

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "member1": "Volodya Vinohradov",
        "member2": "Krystya las_name",
        "member3": "Bronn last_name",
        "member4": "Happy last_name",
        "member5": "Notremmeber last_name",
    })

add_pagination(app)
