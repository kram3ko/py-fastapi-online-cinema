from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.dependencies import get_current_user, require_admin
from crud import orders as order_crud
from database.deps import get_db
from database.models import OrderModel, OrderStatus
from database.models.accounts import UserModel
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatus
from schemas.orders import (
    OrderFilterParams,
    OrderResponse,
    OrderUpdateStatus,
)
from schemas.payments import CheckoutSessionResponse
from services.stripe_service import StripeService

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


@router.post("/{order_id}/pay", response_model=CheckoutSessionResponse)
async def process_order_payment_endpoint(
    request: Request,
    order_id: int = Path(
        ..., gt=0, description="The ID of the order to pay for"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> CheckoutSessionResponse:
    """
    Initiates the payment process for a pending order.
    Creates a Stripe checkout session and returns the payment URL.
    """
    order = await order_crud.get_order_detail(db, order_id, current_user.id)

    if order.status == OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already paid.",
        )
    if order.status == OrderStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pay for a canceled order.",
        )

    session_data = await StripeService.create_checkout_session(request, order)

    payment = PaymentModel(
        user_id=current_user.id,
        order_id=order.id,
        status=PaymentStatus.PENDING,
        amount=order.total_amount,
        external_payment_id=session_data.external_payment_id
    )
    db.add(payment)
    await db.flush()

    payment_items = []
    for item in order.order_items:
        payment_item = PaymentItemModel(
            payment_id=payment.id,
            order_item_id=item.id,
            price_at_payment=item.price_at_order
        )
        payment_items.append(payment_item)
    db.add_all(payment_items)
    await db.commit()

    return CheckoutSessionResponse(
        payment_url=session_data.payment_url,
        external_payment_id=session_data.external_payment_id,
        payment_id=payment.id
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
