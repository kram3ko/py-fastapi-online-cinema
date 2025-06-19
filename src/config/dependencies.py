import os
from collections.abc import Awaitable
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from config.settings import BaseAppSettings, Settings, TestingSettings
from database.deps import get_db
from database.models.accounts import UserGroupEnum, UserModel
from exceptions import TokenExpiredError
from notifications.emails import EmailSender, EmailSenderInterface
from notifications.stripe_notificator import StripeEmailNotificator, StripeEmailSenderInterface
from security.http import get_token
from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from services.payment_webhook_service import PaymentWebhookService
from storages import DropboxStorageInterface, S3StorageInterface
from storages.dropbox import DropboxStorageClient
from storages.s3 import S3StorageClient


def get_settings() -> Settings:
    """
    Retrieve the application settings based on the current environment.

    This function reads the 'ENVIRONMENT' environment variable (defaulting to 'developing' if not set)
    and returns a corresponding settings instance. If the environment is 'testing', it returns an instance
    of TestingSettings; otherwise, it returns an instance of Settings.

    Returns:
        Settings: The settings instance appropriate for the current environment.
    """
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        return TestingSettings()  # type: ignore
    return Settings()


def get_jwt_auth_manager(
    settings: Settings = Depends(get_settings),
) -> JWTAuthManagerInterface:
    """
    Create and return a JWT authentication manager instance.

    This function uses the provided application settings to instantiate a JWTAuthManager, which implements
    the JWTAuthManagerInterface. The manager is configured with secret keys for access and refresh tokens
    as well as the JWT signing algorithm specified in the settings.

    Args:
        settings (Settings, optional): The application settings instance.
        Defaults to the output of get_settings().

    Returns:
        JWTAuthManagerInterface: An instance of JWTAuthManager configured with
        the appropriate secret keys and algorithm.
    """
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )


def get_accounts_email_notificator(
    settings: BaseAppSettings,
) -> EmailSenderInterface:
    """
    Retrieve an instance of the EmailSenderInterface configured with the application settings.

    This function creates an EmailSender using the provided settings, which include details such as the email host,
    port, credentials, TLS usage, and the directory and filenames for email templates. This allows the application
    to send various email notifications (e.g., activation, password reset) as required.

    Args:
        settings (BaseAppSettings): The application settings.

    Returns:
        EmailSenderInterface: An instance of EmailSender configured with the appropriate email settings.
    """
    return EmailSender(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        email=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        template_dir=settings.PATH_TO_EMAIL_TEMPLATES_DIR,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
        password_email_template_name=settings.PASSWORD_RESET_TEMPLATE_NAME,
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME,
    )


def get_s3_storage_client(
    settings: BaseAppSettings = Depends(get_settings),
) -> S3StorageInterface:
    """
    Retrieve an instance of the S3StorageInterface configured with the application settings.

    This function instantiates an S3StorageClient using the provided settings, which include the S3 endpoint URL,
    access credentials, and the bucket name. The returned client can be used to interact with an S3-compatible
    storage service for file uploads and URL generation.

    Args:
        settings (BaseAppSettings, optional): The application settings,
        provided via dependency injection from `get_settings`.

    Returns:
        S3StorageInterface: An instance of S3StorageClient configured with the appropriate S3 storage settings.
    """
    return S3StorageClient(
        endpoint_url=settings.S3_STORAGE_ENDPOINT,
        access_key=settings.S3_STORAGE_ACCESS_KEY,
        secret_key=settings.S3_STORAGE_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
    )


def get_dropbox_storage_client(
    settings: BaseAppSettings = Depends(get_settings),
) -> DropboxStorageInterface:
    """
    Retrieve an instance of the storage interface configured with Dropbox settings.

    This function instantiates a DropboxStorageClient using the provided settings, which include the Dropbox
    access token, app key, app secret, and refresh token. The returned client can be used to interact with Dropbox
    storage service for file uploads and URL generation.

    Args:
        settings (BaseAppSettings, optional): The application settings,
        provided via dependency injection from `get_settings`.

    Returns:
        S3StorageInterface: An instance of DropboxStorageClient configured with the appropriate Dropbox settings.
    """
    return DropboxStorageClient(
        access_token=settings.DROPBOX_ACCESS_TOKEN,
        app_key=settings.DROPBOX_APP_KEY,
        app_secret=settings.DROPBOX_APP_SECRET,
        refresh_token=settings.DROPBOX_REFRESH_TOKEN
    )


def get_stripe_email_notificator(
    settings: BaseAppSettings = Depends(get_settings),
) -> StripeEmailSenderInterface:
    """
     Retrieve an instance of the StripeEmailSenderInterface configured with the application settings.

    This function creates a StripeEmailNotificator using the provided settings,
    which include details such as the email host,
     port, credentials, TLS usage, and the directory for email templates. This allows the application
     to send payment-related email notifications.

     Args:
         settings (BaseAppSettings): The application settings.

     Returns:
         StripeEmailSenderInterface: An instance of StripeEmailNotificator
         configured with the appropriate email settings.
    """
    return StripeEmailNotificator(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        email=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        template_dir=settings.PATH_TO_EMAIL_TEMPLATES_DIR,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
        password_email_template_name=settings.PASSWORD_RESET_TEMPLATE_NAME,
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME,
    )


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_token),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> UserModel:
    """
    Dependency that verifies the JWT token and returns the current user.
    """
    try:
        payload = jwt_manager.decode_access_token(token)
        user_id: int = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        user = await db.scalar(
            select(UserModel).options(joinedload(UserModel.group)).where(UserModel.id == user_id)
        )

        if not isinstance(user, UserModel):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def require_moderator(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.group.name != UserGroupEnum.MODERATOR:
        raise HTTPException(status_code=403, detail="Access forbidden: moderator or admins only")
    return current_user


async def require_admin(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Access forbidden: admins only")
    return current_user


def allow_roles(*roles) -> Callable[..., Awaitable[UserModel]]:
    async def dependency(user: UserModel = Depends(get_current_user)) -> UserModel:
        if user.group.name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have the required permissions to perform this action. "
            )
        return user

    return dependency


def get_webhook_service() -> PaymentWebhookService:
    """Dependency for getting PaymentWebhookService instance."""
    return PaymentWebhookService()
