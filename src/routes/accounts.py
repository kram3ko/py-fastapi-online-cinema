from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import BaseAppSettings, get_jwt_auth_manager, get_settings
from config.dependencies import get_current_user, require_admin
from crud.user_service import UserService
from database.deps import get_db
from database.models.accounts import (
    RefreshTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
)
from scheduler.tasks import (
    send_activation_complete_email_task,
    send_activation_email_task,
    send_password_reset_complete_email_task,
    send_password_reset_email_task,
)
from schemas.accounts import (
    ChangeUserGroupRequest,
    MessageResponseSchema,
    PasswordResetCompleteRequestSchema,
    PasswordResetRequestSchema,
    ResendActivationRequestSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    UserActivationRequestSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
)
from security.http import jwt_security
from security.interfaces import JWTAuthManagerInterface

router = APIRouter()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    summary="User Registration",
    description="Register a new user with an email and password.",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "Conflict - User with this email already exists.",
            "content": {
                "application/json": {"example": {"detail": "A user with this email test@example.com already exists."}}
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred during user creation.",
            "content": {"application/json": {"example": {"detail": "An error occurred during user creation."}}},
        },
    },
)
async def register_user(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
) -> UserRegistrationResponseSchema:
    """
    Endpoint for user registration.

    Registers a new user, hashes their password, and assigns them to the default user group.
    If a user with the same email already exists, an HTTP 409 error is raised.
    In case of any unexpected issues during the creation process, an HTTP 500 error is returned.

    Args:
        user_data (UserRegistrationRequestSchema): The registration details including email and password.
        db (AsyncSession): The asynchronous database session.
        settings (BaseAppSettings): The application settings.

    Returns:
        UserRegistrationResponseSchema: The newly created user's details.

    Raises:
        HTTPException:
            - 409 Conflict if a user with the same email exists.
            - 500 Internal Server Error if an error occurs during user creation.
    """
    user_service = UserService(db)

    # Check if user exists
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"A user with this email {user_data.email} already exists."
        )

    user_group = db.scalar(select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER))

    if not user_group:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Default user group not found.")

    try:
        new_user = await user_service.create_user(user_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during user creation."
        ) from e

    activation_link = f"{settings.FRONTEND_URL}/accounts/activate/"
    send_activation_email_task.delay(new_user.email, activation_link)

    return UserRegistrationResponseSchema.model_validate(new_user)


@router.post(
    "/activate/",
    response_model=MessageResponseSchema,
    summary="Activate User Account",
    description="Activate a user's account using their email and activation token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The activation token is invalid or expired,"
                           " or the user account is already active.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid Token",
                            "value": {"detail": "Invalid or expired activation token."},
                        },
                        "already_active": {
                            "summary": "Account Already Active",
                            "value": {"detail": "User account is already active."},
                        },
                    }
                }
            },
        },
    },
)
async def activate_account(
    activation_data: UserActivationRequestSchema,
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
) -> MessageResponseSchema:
    """Endpoint to activate a user's account."""
    user_service = UserService(db)

    result = await user_service.activate_user(activation_data)
    if result == "already_active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User account is already active.")
    if result == "invalid_token":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired activation token.")

    login_link = f"{settings.FRONTEND_URL}/accounts/login/"
    send_activation_complete_email_task.delay(str(activation_data.email), login_link)

    return MessageResponseSchema(message="User account activated successfully.")


@router.post(
    "/activate/resend/",
    response_model=MessageResponseSchema,
    summary="Resend Activation Email",
    description="Resend a new activation link if the previous one expired.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - User account is already active.",
            "content": {"application/json": {"example": {"detail": "User account is already active."}}},
        },
    },
)
async def resend_activation_email(
    data: ResendActivationRequestSchema,
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
) -> MessageResponseSchema:
    """
    Endpoint to resend activation email.

    This endpoint verifies the activation token for a user by checking that the token record exists
    and that it has not expired. If the token is valid and the user's account is not already active,
    the user's account is activated and the activation token is deleted. If the token is invalid, expired,
    or if the account is already active, an HTTP 400 error is raised.

    Args:
        data (ResendActivationRequestSchema): Contains the user's email.
        db (AsyncSession): The asynchronous database session.
        settings (BaseAppSettings): The application settings.
    Returns:
        MessageResponseSchema: A response message confirming that an email will be sent with instructions.

    Raises:
        HTTPException: If the user account is already active.
    """
    user_service = UserService(db)

    if not await user_service.resend_activation(data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User account is already active.")

    activation_link = f"{settings.FRONTEND_URL}/accounts/activate/"
    send_activation_email_task.delay(data.email, activation_link)

    return MessageResponseSchema(message="If you are registered, you will receive an email with instructions.")


@router.post(
    "/password-reset/request/",
    response_model=MessageResponseSchema,
    summary="Request Password Reset Token",
    description="Allows a user to request a password reset token.",
    status_code=status.HTTP_200_OK,
)
async def request_password_reset_token(
    data: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
) -> MessageResponseSchema:
    """
    Endpoint to request a password reset token.
    """
    user_service = UserService(db)

    if await user_service.request_password_reset(data):
        reset_link = f"{settings.FRONTEND_URL}/accounts/reset-password/"
        send_password_reset_email_task.delay(str(data.email), reset_link)

    return MessageResponseSchema(message="If you are registered, you will receive an email with instructions.")


@router.post(
    "/reset-password/complete/",
    response_model=MessageResponseSchema,
    summary="Reset User Password",
    description="Reset a user's password if a valid token is provided.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The provided email or token is invalid.",
            "content": {"application/json": {"example": {"detail": "Invalid email or token."}}},
        },
        500: {
            "description": "Internal Server Error - An error occurred while resetting the password.",
            "content": {
                "application/json": {"example": {"detail": "An error occurred while resetting the password."}}
            },
        },
    },
)
async def reset_password(
    data: PasswordResetCompleteRequestSchema,
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
) -> MessageResponseSchema:
    """Endpoint to reset a user's password."""
    user_service = UserService(db)

    result = await user_service.reset_password(data)
    if result == "commit_error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while resetting the password."
        )
    if result in {"invalid", "inactive"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token.")

    login_link = f"{settings.FRONTEND_URL}/accounts/login/"
    send_password_reset_complete_email_task.delay(str(data.email), login_link)

    return MessageResponseSchema(message="Password has been reset successfully.")


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    summary="User Login",
    description="Authenticate a user and return access and refresh tokens.",
    status_code=status.HTTP_200_OK,
    responses={
        401: {
            "description": "Unauthorized - Invalid email or password.",
            "content": {"application/json": {"example": {"detail": "Invalid email or password."}}},
        },
        403: {
            "description": "Forbidden - User account is not activated.",
            "content": {"application/json": {"example": {"detail": "User account is not activated."}}},
        },
        500: {
            "description": "Internal Server Error - An error occurred while processing the request.",
            "content": {
                "application/json": {"example": {"detail": "An error occurred while processing the request."}}
            },
        },
    },
)
async def login_user(
    login_data: UserLoginRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> UserLoginResponseSchema:
    """Endpoint for user login."""
    user_service = UserService(db)

    try:
        access_token, refresh_token, error = await user_service.login_user(login_data, jwt_manager)
        if error == "inactive":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not activated.")
        if error == "commit_error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing the request.",
            )
        if not access_token or not refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while processing the request."
        )

    return UserLoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
    summary="Refresh Access Token",
    description="Refresh the access token using a valid refresh token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The provided refresh token is invalid or expired.",
            "content": {"application/json": {"example": {"detail": "Token has expired."}}},
        },
        401: {
            "description": "Unauthorized - Refresh token not found.",
            "content": {"application/json": {"example": {"detail": "Refresh token not found."}}},
        },
        404: {
            "description": "Not Found - The user associated with the token does not exist.",
            "content": {"application/json": {"example": {"detail": "User not found."}}},
        },
    },
)
async def refresh_access_token(
    token_data: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> TokenRefreshResponseSchema:
    """Endpoint to refresh an access token."""
    user_service = UserService(db)

    access_token, error = await user_service.refresh_access_token(token_data, jwt_manager)
    if error == "expired":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired.")
    if error == "not_found":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found.")
    if error == "user_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return TokenRefreshResponseSchema(access_token=access_token)


@router.post(
    "/logout/",
    response_model=MessageResponseSchema,
    summary="User Logout",
    description="Logout user and invalidate all their refresh tokens.",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(jwt_security)]
)
async def logout_user(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> MessageResponseSchema:
    """Endpoint for user logout."""
    try:
        # Delete all refresh tokens for the current user
        refresh_tokens = (await db.scalars(
            select(RefreshTokenModel).where(RefreshTokenModel.user_id == current_user.id)
        )).all()

        for token in refresh_tokens:
            await db.delete(token)

        await db.commit()
        return MessageResponseSchema(message="Successfully logged out.")
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout."
        )


@router.post("/users/{user_id}/change_group")
async def change_user_group(
    user_id: int,
    user_group: ChangeUserGroupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
) -> MessageResponseSchema:
    user_obj = await db.scalar(select(UserModel).where(UserModel.id == user_id))
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    new_group = await db.scalar(select(UserGroupModel).where(UserGroupModel.name == user_group.group))
    if not new_group:
        raise HTTPException(status_code=500, detail="Group not found")

    user_obj.group = new_group
    await db.commit()
    return MessageResponseSchema(message=f"User group changed to {user_group.group.value}")
