from fastapi import Depends

from config.dependencies import get_current_user
from database.models import UserGroupEnum, UserModel


async def get_current_user_is_admin(
    user: UserModel = Depends(get_current_user),
) -> bool:
    is_admin = user.group.name == UserGroupEnum.ADMIN
    return is_admin