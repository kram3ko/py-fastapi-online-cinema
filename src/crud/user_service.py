from datetime import datetime, timezone
from typing import Optional, cast

from pydantic import EmailStr
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from config import get_settings
from database.models.accounts import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
)
from exceptions import BaseSecurityError
from schemas.accounts import (
    PasswordResetCompleteRequestSchema,
    PasswordResetRequestSchema,
    ResendActivationRequestSchema,
    TokenRefreshRequestSchema,
    UserActivationRequestSchema,
    UserLoginRequestSchema,
    UserRegistrationRequestSchema,
)
from security.interfaces import JWTAuthManagerInterface


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def create_user(self, user: UserRegistrationRequestSchema) -> UserModel:
        """Create a new user with activation token."""
        try:
            result = await self.db.execute(select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER))
            group = result.scalar_one()
            db_user = UserModel.create(email=str(user.email), raw_password=user.password, group_id=group.id)

            self.db.add(db_user)
            await self.db.flush()

            activation_token = ActivationTokenModel(user_id=db_user.id)
            self.db.add(activation_token)
            await self.db.commit()
            await self.db.refresh(db_user)

            return db_user
        except Exception:
            await self.db.rollback()
            raise

    async def get_user_by_email(self, email: EmailStr) -> Optional[UserModel]:
        """Get user by email."""
        result = await self.db.execute(select(UserModel).where(UserModel.email == email))
        return result.scalar_one_or_none()

    async def activate_user(self, activation_data: UserActivationRequestSchema) -> str:
        """Activate user account using activation token.
        Returns: 'success', 'already_active', or 'invalid_token'"""
        token_record = await self.db.scalar(
            select(ActivationTokenModel)
            .options(joinedload(ActivationTokenModel.user))
            .join(UserModel)
            .where(UserModel.email == activation_data.email, ActivationTokenModel.token == activation_data.token)
        )

        now_utc = datetime.now(timezone.utc)
        if not token_record or cast(datetime, token_record.expires_at).replace(tzinfo=timezone.utc) < now_utc:
            user = await self.get_user_by_email(activation_data.email)
            if user and user.is_active:
                return "already_active"
            if token_record:
                await self.db.delete(token_record)
                await self.db.commit()
            return "invalid_token"

        user = token_record.user
        if user.is_active:
            return "already_active"

        user.is_active = True
        await self.db.delete(token_record)
        await self.db.commit()
        return "success"

    async def resend_activation(self, data: ResendActivationRequestSchema) -> bool:
        """Resend activation email."""
        user = await self.get_user_by_email(data.email)
        if not user or user.is_active:
            return False

        await self.db.execute(delete(ActivationTokenModel).where(ActivationTokenModel.user_id == user.id))
        activation_token = ActivationTokenModel(user_id=user.id)
        self.db.add(activation_token)
        await self.db.commit()
        return True

    async def request_password_reset(self, data: PasswordResetRequestSchema) -> bool:
        """Request password reset token."""
        user = await self.get_user_by_email(data.email)
        if not user or not user.is_active:
            return False

        await self.db.execute(delete(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user.id))
        reset_token = PasswordResetTokenModel(user_id=user.id)
        self.db.add(reset_token)
        await self.db.commit()
        return True

    async def reset_password(self, data: PasswordResetCompleteRequestSchema) -> str:
        """Reset user password using reset token. Returns: 'success', 'invalid', 'inactive', 'commit_error'"""
        token_record = await self.db.scalar(
            select(PasswordResetTokenModel)
            .options(joinedload(PasswordResetTokenModel.user))
            .join(UserModel)
            .where(UserModel.email == data.email, PasswordResetTokenModel.token == data.token)
        )

        now_utc = datetime.now(timezone.utc)
        if not token_record or cast(datetime, token_record.expires_at).replace(tzinfo=timezone.utc) < now_utc:
            user = await self.get_user_by_email(data.email)
            if user:
                await self.db.execute(
                    delete(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user.id)
                )
                await self.db.commit()
            return "invalid"

        user = token_record.user
        if not user.is_active:
            return "inactive"

        try:
            user.password = data.password
            await self.db.delete(token_record)
            await self.db.commit()
            return "success"
        except SQLAlchemyError:
            await self.db.rollback()
            return "commit_error"

    async def login_user(
        self, login_data: UserLoginRequestSchema, jwt_manager: JWTAuthManagerInterface
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Authenticate user and return access and refresh tokens, plus error code."""
        user = await self.get_user_by_email(login_data.email)
        if not user or not user.verify_password(login_data.password):
            return None, None, None

        if not user.is_active:
            return None, None, "inactive"

        jwt_refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})
        try:
            refresh_token = RefreshTokenModel.create(
                user_id=user.id, days_valid=self.settings.LOGIN_TIME_DAYS, token=jwt_refresh_token
            )
            self.db.add(refresh_token)
            await self.db.flush()
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            return None, None, "commit_error"

        jwt_access_token = jwt_manager.create_access_token({"user_id": user.id})
        return jwt_access_token, jwt_refresh_token, None

    async def refresh_access_token(
        self, token_data: TokenRefreshRequestSchema, jwt_manager: JWTAuthManagerInterface
    ) -> tuple:
        """Refresh access token using refresh token. Returns: (access_token, error_code)"""
        try:
            decoded_token = jwt_manager.decode_refresh_token(token_data.refresh_token)
            user_id = decoded_token.get("user_id")
        except BaseSecurityError:
            return None, "expired"

        refresh_token_record = await self.db.scalar(
            select(RefreshTokenModel).filter_by(token=token_data.refresh_token)
        )
        if not refresh_token_record:
            return None, "not_found"

        user = await self.db.scalar(select(UserModel).filter_by(id=user_id))
        if not user:
            return None, "user_not_found"

        return jwt_manager.create_access_token({"user_id": user_id}), None
