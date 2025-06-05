from fastapi import FastAPI
from fastapi_pagination import add_pagination

from routes import accounts_router, movie_router, profiles_router

app = FastAPI(title="Online Cinema", description="Group project Online Cinema API")

api_version_prefix = "/api/v1"

app.include_router(accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"])
app.include_router(profiles_router, prefix=f"{api_version_prefix}/profiles", tags=["profiles"])
app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])

add_pagination(app)
