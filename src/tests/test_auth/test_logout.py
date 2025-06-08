import pytest
import pytest_asyncio
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from pydantic_settings import BaseSettings

from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from src.main import app
from src.database.models.accounts import RefreshTokenModel, UserModel


@pytest_asyncio.fixture(scope="function", autouse=True)
async def test_user(
    reset_db,
    client,
    seed_user_groups,
    db_session,
    settings,
):
    user = UserModel(
        id=1,
        email="testuser@example.com",
        _hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    jwt_manager = JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM
    )

    access_token = jwt_manager.create_access_token({"user_id": user.id})
    refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})

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

@pytest.mark.asyncio
async def test_logout_success(test_user, mocker, test_db: AsyncSession):
    # Mock dependencies
    mocker.patch("src.config.dependencies.get_current_user", return_value=test_user["user"])
    mocker.patch("src.database.deps.get_db", return_value=test_db)

    # Call the logout endpoint with valid access token
    response = client.post(
        "/logout/",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
    )

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"message": "User logged out successfully."}

    # Verify refresh tokens are deleted
    tokens = await test_db.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.user_id == test_user["user"].id)
    )
    assert tokens.scalars().all() == []

    # Verify cookie is cleared
    assert response.cookies["Authorization"] == ""

@pytest.mark.asyncio
async def test_logout_unauthorized(mocker):
    # Mock dependencies to simulate no user
    mocker.patch("src.config.dependencies.get_current_user", side_effect=Exception("Unauthorized"))

    # Call the logout endpoint without valid access token
    response = client.post("/logout/")

    # Assertions
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}