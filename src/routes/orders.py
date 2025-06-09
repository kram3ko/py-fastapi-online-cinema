from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.session_postgresql import get_postgresql_db
from crud import orders as order_crud
from schemas.orders import (
    OrderResponse,
    OrderFilterParams,
    OrderUpdateStatus
)
from database.models.accounts import UserModel
# from security.dependencies import get_current_user, require_admin
from database.models.orders import OrderStatus


# temporary solution
async def get_current_user() -> UserModel:
    return UserModel(id=1, email="demo@example.com", hashed_password="123", is_active=True, group_id=1)


# temporary solution
async def require_admin(current_user: UserModel):
    """
    Dependency to ensure the user is an admin.
    """
    ADMIN_GROUP_ID = 3  # replace with the actual ID for ADMIN in your DB

    if not current_user.group_id == ADMIN_GROUP_ID:
        print("not admin")


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await order_crud.create_order_from_cart(current_user.id, db)


@router.get("/", response_model=List[OrderResponse])
async def list_user_orders(
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await order_crud.get_user_orders(current_user.id, db)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(
    order_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await order_crud.get_order_detail(db, order_id, current_user.id)


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await order_crud.cancel_order(db, order_id, current_user.id)

# ---------- ADMIN ROUTES ----------

# @router.get("/admin/", response_model=List[OrderResponse], dependencies=[Depends(require_admin)])
# async def admin_list_orders(
#     user_id: int = Query(None),
#     status: OrderStatus = Query(None),
#     start_date: str = Query(None),
#     end_date: str = Query(None),
#     db: AsyncSession = Depends(get_postgresql_db)
# ):
#     return await order_crud.get_all_orders(db, user_id, start_date, end_date, status)


# @router.patch("/admin/{order_id}", response_model=OrderResponse, dependencies=[Depends(require_admin)])
# async def admin_update_order_status(
#     order_id: int,
#     status_data: OrderUpdateStatus,
#     db: AsyncSession = Depends(get_postgresql_db)
# ):
#     return await order_crud.update_order_status(db, order_id, status_data.status)
