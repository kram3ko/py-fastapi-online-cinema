from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.dependencies import get_current_user, require_admin
from crud import orders as order_crud
from database.deps import get_db
from database.models import OrderModel
from database.models.accounts import UserModel
from schemas.orders import (
    OrderFilterParams,
    OrderResponse,
    OrderUpdateStatus,
)

router = APIRouter()


@router.post(
    "/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED
)
async def create_order(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderModel:
    """
    Places a new order for the current user based on their shopping cart.
    The cart will be cleared upon successful order creation.
    """
    # The CRUD function handles validation and raises HTTPException if the cart is empty or invalid.
    order = await order_crud.create_order_from_cart(current_user.id, db)
    return order


@router.get("/", response_model=list[OrderResponse])
async def list_user_orders(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> list[OrderModel]:
    """
    Retrieves a list of all orders for the current user.
    """
    return await order_crud.get_user_orders(current_user.id, db)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(
    order_id: int = Path(
        ..., gt=0, description="The ID of the order to retrieve"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderModel:
    """
    Retrieves details of a specific order for the current user.
    Users can only access their own orders.
    """
    return await order_crud.get_order_detail(db, order_id, current_user.id)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order_endpoint(  # Renamed to avoid conflict with crud.cancel_order
    order_id: int = Path(
        ..., gt=0, description="The ID of the order to cancel"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderModel:
    """
    Cancels a pending order for the current user.
    Paid or already canceled orders cannot be canceled directly.
    """
    return await order_crud.cancel_order(db, order_id, current_user.id)


@router.post("/{order_id}/pay", response_model=OrderResponse)
async def process_order_payment_endpoint(  # Renamed to avoid conflict with crud.process_order_payment
    order_id: int = Path(
        ..., gt=0, description="The ID of the order to pay for"
    ),
    # payment_data: OrderPaymentRequest, # You can uncomment and use this if your payment endpoint needs a request body
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderModel:
    """
    Initiates the payment process for a pending order.
    Upon successful payment, the order status will be updated to PAID.
    """
    return await order_crud.process_order_payment(
        db, order_id, current_user.id
    )


# --- ADMIN-SPECIFIC ROUTES ---


@router.get(
    "/admin/",
    response_model=list[OrderResponse],
    dependencies=[Depends(require_admin)],
)
async def admin_list_orders(
    # FastAPI automatically handles the dependency injection and validation for Query parameters
    # when using a Pydantic model with Depends()
    filters: OrderFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> OrderModel:
    """
    Admin: Retrieves a list of all orders with optional filtering capabilities.
    Filters can be applied by user ID, creation date range, and order status.
    Requires administrator privileges.
    """
    return await order_crud.get_all_orders(
        db,
        user_id=filters.user_id,
        start_date=filters.start_date,
        end_date=filters.end_date,
        status=filters.status,
    )


@router.patch(
    "/admin/{order_id}/status",
    response_model=OrderResponse,
    dependencies=[Depends(require_admin)],
)
async def admin_update_order_status(
    status_data: OrderUpdateStatus,
    order_id: int = Path(
        ..., gt=0, description="The ID of the order to update"
    ),
    db: AsyncSession = Depends(get_db),
) -> OrderModel:
    """
    Admin: Updates the status of a specific order.
    Requires administrator privileges.
    """
    return await order_crud.update_order_status(
        db, order_id, status_data.status
    )
