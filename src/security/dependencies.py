from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.models.accounts import UserModel
from security.http import get_token
from security.token_manager import JWTAuthManager
from config.settings import settings


auth_manager = JWTAuthManager(
    secret_key_access=settings.JWT_SECRET_KEY_ACCESS,
    secret_key_refresh=settings.JWT_SECRET_KEY_REFRESH,
    algorithm=settings.JWT_ALGORITHM,
)


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(get_token)
) -> UserModel:
    """
    Dependency that verifies the JWT token and returns the current user.

    Args:
        db: Database session
        token: JWT token from the Authorization header

    Returns:
        UserModel: The current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:

        payload = auth_manager.decode_access_token(token)
        user_id: int = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        user = await db.get(UserModel, user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
