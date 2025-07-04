from typing import cast

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.dependencies import get_current_user, get_dropbox_storage_client
from database.deps import get_db
from database.models.accounts import GenderEnum, UserGroupEnum, UserGroupModel, UserModel, UserProfileModel
from exceptions import S3FileUploadError
from schemas.profiles import ProfileCreateRequestSchema, ProfileResponseSchema
from storages import DropboxStorageInterface

router = APIRouter()


@router.post(
    "/users/{user_id}/profile/",
    response_model=ProfileResponseSchema,
    summary="Create user profile",
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    user_id: int,
    profile_data: ProfileCreateRequestSchema = Form(..., media_type="multipart/form-data"),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    dropbox: DropboxStorageInterface = Depends(get_dropbox_storage_client),
) -> ProfileResponseSchema:
    """
    Creates a user profile.

    Steps:
    - Validate user authentication token.
    - Check if the user already has a profile.
    - Upload avatar to S3 storage.
    - Store profile details in the database.

    Args:
        user_id (int): The ID of the user for whom the profile is being created.
        profile_data (ProfileCreateRequestSchema): The profile data from the form.
        user (UserModel): The authenticated user.
        db (AsyncSession): The asynchronous database session.
        dropbox (DropboxStorageInterface): The Dropbox storage client.

    Returns:
        ProfileResponseSchema: The created user profile details.

    Raises:
        HTTPException: If authentication fails, if the user is not found or inactive,
                       or if the profile already exists, or if S3 upload fails.
    """
    if user_id != user.id:
        user_group = await db.scalar(select(UserGroupModel).join(UserModel).where(UserModel.id == user.id))

        if not user_group or user_group.name == UserGroupEnum.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to edit this profile."
            )

    user = await db.scalar(select(UserModel).where(UserModel.id == user_id))

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or not active.")

    existing_profile = await db.scalar(select(UserProfileModel).where(UserProfileModel.user_id == user.id))
    if existing_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a profile.")

    avatar_bytes = await profile_data.avatar.read()
    avatar_key = f"avatars/{user.id}_{profile_data.avatar.filename}"

    try:
        await dropbox.upload_file(file_name=avatar_key, file_data=avatar_bytes)
    except S3FileUploadError as e:
        print(f"Error uploading avatar to S3: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar. Please try again later.",
        )

    new_profile = UserProfileModel(
        user_id=cast(int, user.id),
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        gender=cast(GenderEnum, profile_data.gender),
        date_of_birth=profile_data.date_of_birth,
        info=profile_data.info,
        avatar=avatar_key,
    )

    db.add(new_profile)
    await db.commit()

    avatar_url = await dropbox.get_file_url(new_profile.avatar)

    return ProfileResponseSchema(
        id=new_profile.id,
        user_id=new_profile.user_id,
        first_name=new_profile.first_name,
        last_name=new_profile.last_name,
        gender=new_profile.gender,
        date_of_birth=new_profile.date_of_birth,
        info=new_profile.info,
        avatar=cast(HttpUrl, avatar_url),
    )
