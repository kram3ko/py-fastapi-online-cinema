from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_jwt_auth_manager
from database import get_db
from database.models.accounts import UserModel
from security.http import get_token
from security.interfaces import JWTAuthManagerInterface


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_token),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> UserModel:
    """
    Dependency that verifies the JWT token and returns the current user.

    Args:
        db: Database session
        token: JWT token from the Authorization header
        jwt_manager: JWT authorization manager

    Returns:
        UserModel: The current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = jwt_manager.decode_access_token(token)
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

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
