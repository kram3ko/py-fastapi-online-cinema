from fastapi import FastAPI
from fastapi_pagination import add_pagination

from routes.accounts import router as accounts_router
from routes.index import router as index_router
from routes.movies import router as movie_router
from routes.orders import router as orders_router
from routes.payments import router as payments_router
from routes.profiles import router as profiles_router
from routes.shopping_cart import router as cart_router

app = FastAPI(title="Online Cinema", description="Group project Online Cinema API")

api_version_prefix = "/api/v1"

app.include_router(index_router, tags=["index"])
app.include_router(accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"])
app.include_router(profiles_router, prefix=f"{api_version_prefix}/profiles", tags=["profiles"])
app.include_router(movie_router, prefix=f"{api_version_prefix}/online_cinema", tags=["movies"])
app.include_router(payments_router, prefix=f"{api_version_prefix}/payments", tags=["payments"])
app.include_router(cart_router, prefix=f"{api_version_prefix}/cart", tags=["cart"])
app.include_router(orders_router, prefix=f"{api_version_prefix}/orders", tags=["orders"])

add_pagination(app)
