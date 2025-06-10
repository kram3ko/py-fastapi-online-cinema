import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from config.dependencies import get_current_user
from security.token_manager import JWTAuthManager
from src.main import app
from database.models.accounts import (
    RefreshTokenModel,
    UserModel,
    UserGroupModel,
    UserGroupEnum
)


@pytest_asyncio.fixture(scope="function")
async def test_user(
    seed_user_groups,
    db_session,
    settings,
):
    query = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    result = await db_session.execute(query)
    user_group = result.scalars().first()
    user = UserModel(
        id=1,
        email="testuser@example.com",
        _hashed_password="hashed_password",
        is_active=True,
        group=user_group
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    jwt_manager = JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM
    )

    access_token = jwt_manager.create_access_token({"sub": user.id, "user_id": user.id})
    refresh_token = jwt_manager.create_refresh_token({"sub": user.id, "user_id": user.id})

    refresh_token_record = RefreshTokenModel(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.LOGIN_TIME_DAYS),
    )
    db_session.add(refresh_token_record)
    await db_session.commit()

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@pytest_asyncio.fixture
async def client_logout(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user["user"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_logout_unauthorized(client):
    response = await client.get(
        "api/v1/accounts/logout/",
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authorization header is missing"}

    response = await client.get(
        "api/v1/accounts/logout/",
        headers={"Authorization": f"Bearer wrong_token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.asyncio
async def test_logout_success(test_user, client_logout, seed_user_groups, db_session):
    response = await client_logout.get(
        "api/v1/accounts/logout/",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"message": "User logged out successfully."}

    tokens = await db_session.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.user_id == test_user["user"].id)
    )
    assert tokens.scalars().all() == []

    assert response.cookies.get("Authorization") is None
