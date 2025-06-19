from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.dependencies import get_current_user, require_admin
from crud import orders as order_crud
from crud import shopping_cart as cart_crud
from database.deps import get_db
from database.models.accounts import UserModel
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatus
from exceptions.shopping_cart import (
    CartNotFoundError,
    MovieAlreadyInCartError,
    MovieAlreadyPurchasedError,
    MovieNotFoundError,
    MovieNotInCartError,
)
from schemas.accounts import MessageResponseSchema
from schemas.payments import CheckoutSessionResponse
from schemas.shopping_cart import (
    CartItemCreate,
    CartItemResponse,
    CartResponse,
)
from services.stripe_service import StripeService

router = APIRouter()


@router.get("/", response_model=CartResponse)
async def get_cart(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    """Get current user's shopping cart."""
    cart = await cart_crud.get_or_create_cart(db, current_user.id)
    return cart


@router.post("/items", response_model=CartItemResponse)
async def add_movie_to_cart(
    item: CartItemCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartItemResponse:
    """Add movie to cart."""
    cart = await cart_crud.get_or_create_cart(db, current_user.id)
    cart_item, error = await cart_crud.add_movie_to_cart(
        db, cart.id, item.movie_id, current_user.id
    )

    if error:
        if isinstance(error, MovieNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found",
            )
        elif isinstance(error, MovieAlreadyInCartError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movie is already in cart",
            )
        elif isinstance(error, MovieAlreadyPurchasedError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This movie has already been purchased. Repurchase is not possible.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    return cart_item


@router.delete("/items/{movie_id}", response_model=MessageResponseSchema)
async def remove_movie_from_cart(
    movie_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    """Remove movie from cart."""
    cart = await cart_crud.get_or_create_cart(db, current_user.id)
    success, error = await cart_crud.remove_movie_from_cart(
        db, cart.id, movie_id
    )

    if error:
        if isinstance(error, CartNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found",
            )
        elif isinstance(error, MovieNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found",
            )
        elif isinstance(error, MovieNotInCartError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movie is not in cart",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    return MessageResponseSchema(message="Movie removed from cart")


@router.delete("/", response_model=MessageResponseSchema)
async def clear_cart(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    """Clear all items from cart."""
    cart = await cart_crud.get_or_create_cart(db, current_user.id)
    success, error = await cart_crud.clear_cart(db, cart.id)

    if error:
        if isinstance(error, CartNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    return MessageResponseSchema(message="Cart cleared successfully")


@router.post("/pay", response_model=CheckoutSessionResponse)
async def pay_for_cart(
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutSessionResponse:
    """
    Creates an order from the cart and initiates Stripe payment.
    Returns a URL to the Stripe checkout page.
    """
    order = await order_crud.create_order_from_cart(current_user.id, db)

    session_data = await StripeService.create_checkout_session(request, order)

    payment = PaymentModel(
        user_id=current_user.id,
        order_id=order.id,
        status=PaymentStatus.PENDING,
        amount=order.total_amount,
        session_id=session_data.session_id
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
        session_id=session_data.session_id,
        payment_id=payment.id
    )


@router.get("/admin/user/{user_id}", response_model=CartResponse)
async def get_user_cart_as_admin(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    """Get user's shopping cart (admin only)."""
    cart = await cart_crud.get_or_create_cart(db, user_id)
    return cart
