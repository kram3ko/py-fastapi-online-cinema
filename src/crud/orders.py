from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database.models.accounts import UserModel
from database.models.movies import MovieModel
from database.models.orders import OrderItemModel, OrderModel, OrderStatus
from database.models.payments import (
    PaymentItemModel,
    PaymentModel,
    PaymentStatus,
)
from database.models.shopping_cart import Cart, CartItem


async def get_user_cart_with_items(user_id: int, db: AsyncSession) -> Cart:
    """Get user's cart with its items and movies."""
    cart_result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(joinedload(Cart.items).joinedload(CartItem.movie))
    )
    cart = cart_result.scalars().first()

    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty.",
        )
    return cart


async def get_purchased_movie_ids(user_id: int, db: AsyncSession) -> set[int]:
    """Get set of movie IDs that user has already purchased."""
    purchased_query = await db.execute(
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(
            OrderModel.user_id == user_id,
            OrderModel.status == OrderStatus.PAID,
        )
    )
    return {row[0] for row in purchased_query.all()}


async def get_pending_movie_ids(user_id: int, db: AsyncSession) -> set[int]:
    """Get set of movie IDs that are in user's pending orders."""
    pending_query = await db.execute(
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(
            OrderModel.user_id == user_id,
            OrderModel.status == OrderStatus.PENDING,
        )
    )
    return {row[0] for row in pending_query.all()}


async def process_cart_items(
    cart: Cart,
    purchased_movie_ids: set[int],
    pending_movie_ids: set[int],
    order_id: int,
) -> tuple[list[OrderItemModel], list[dict], float]:
    """Process cart items and create order items."""
    order_items_to_add = []
    excluded_movies_details = []
    total_amount = 0.0

    for item in cart.items:
        if item.movie_id in purchased_movie_ids:
            excluded_movies_details.append({
                "movie_id": item.movie_id,
                "title": item.movie.name,
                "reason": "Already purchased",
            })
            continue

        if item.movie_id in pending_movie_ids:
            excluded_movies_details.append({
                "movie_id": item.movie_id,
                "title": item.movie.name,
                "reason": "Already in a pending order",
            })
            continue

        order_item = OrderItemModel(
            order_id=order_id,
            movie_id=item.movie_id,
            price_at_order=item.movie.price,
        )
        order_items_to_add.append(order_item)
        total_amount += float(item.movie.price)

    return order_items_to_add, excluded_movies_details, total_amount


async def clear_cart_items(cart: Cart, db: AsyncSession) -> None :
    """Clear all items from the cart."""
    for item in cart.items:
        await db.delete(item)
    await db.commit()


async def create_order_from_cart(user_id: int, db: AsyncSession) -> OrderModel:
    """
    Creates a new order for a user based on their current shopping cart.
    Handles movie availability, purchased movies, and pending orders.

    Raises:
        HTTPException: If the cart is empty, or if no valid movies can be added to the order.
    """

    # Get cart and validate
    cart = await get_user_cart_with_items(user_id, db)

    # Get purchased and pending movies
    purchased_movie_ids = await get_purchased_movie_ids(user_id, db)
    pending_movie_ids = await get_pending_movie_ids(user_id, db)

    # Create new order
    new_order = OrderModel(user_id=user_id)
    db.add(new_order)
    await db.flush()

    # Process cart items
    order_items_to_add, excluded_movies_details, total_amount = await process_cart_items(
        cart, purchased_movie_ids, pending_movie_ids, new_order.id
    )

    if not order_items_to_add:
        await db.rollback()
        detail_msg = "No valid movies to add to order."
        if excluded_movies_details:
            detail_msg += f" Excluded: {excluded_movies_details}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=detail_msg
        )

    # Add order items and update total
    db.add_all(order_items_to_add)
    new_order.total_amount = total_amount
    await db.commit()

    # Clear cart
    await clear_cart_items(cart, db)

    if excluded_movies_details:
        print(f"Warning: Some movies were excluded from the order: {excluded_movies_details}")

    # Return complete order with relationships
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == new_order.id)
        .options(
            selectinload(OrderModel.order_items).selectinload(OrderItemModel.movie),
            selectinload(OrderModel.user).selectinload(UserModel.profile),
        )
    )
    return result.scalar_one()


async def get_user_orders(user_id: int, db: AsyncSession) -> list[OrderModel]:
    """
    Retrieves all orders for a specific user, with loaded related data.
    """
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.user_id == user_id)
        .options(
            selectinload(OrderModel.order_items).selectinload(OrderItemModel.movie),
            selectinload(OrderModel.user).selectinload(UserModel.profile),
        )
        .order_by(OrderModel.created_at.desc())
    )
    return list(result.scalars().all())


async def get_order_detail(
    db: AsyncSession, order_id: int, user_id: int
) -> OrderModel:
    """
    Retrieves a specific order by its ID, ensuring the user has access.
    Raises HTTPException if order not found or user unauthorized.
    """
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == order_id, OrderModel.user_id == user_id)
        .options(
            selectinload(OrderModel.order_items)
            .selectinload(OrderItemModel.movie)
            .selectinload(MovieModel.genres),
            selectinload(OrderModel.user).selectinload(UserModel.profile),
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or access denied.",
        )
    return order


async def cancel_order(
    db: AsyncSession, order_id: int, user_id: int
) -> OrderModel:
    """
    Cancels an order (updates its status to CANCELED).
    Raises HTTPException if order not found, already paid/canceled.
    """
    order = await get_order_detail(db, order_id, user_id)

    if order.status == OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid orders can only be canceled via refund request.",
        )
    elif order.status == OrderStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already canceled.",
        )

    order.status = OrderStatus.CANCELED
    await db.commit()
    await db.refresh(order)
    return order


async def process_order_payment(
    db: AsyncSession, order_id: int, user_id: int
) -> OrderModel:
    """
    Processes payment for an order.
    Revalidates total amount, simulates payment, and updates order status to PAID.

    Raises:
        HTTPException: If the order is already paid, canceled, or a movie is unavailable.
    """
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == order_id, OrderModel.user_id == user_id)
        .options(
            selectinload(OrderModel.order_items).selectinload(OrderItemModel.movie),
            selectinload(OrderModel.user).selectinload(UserModel.profile),
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or access denied.",
        )

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

    # Re-validate total amount before processing payment
    recalculated_total = 0.0
    for item in order.order_items:
        # Load the current price of the movie
        movie = await db.get(MovieModel, item.movie_id)
        if not movie or not movie.price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Movie with ID {item.movie_id} in "
                f"order is no longer available or has no price.",
            )

        # Use the current movie price for recalculation
        recalculated_total += float(movie.price)

    payment = PaymentModel(
        user_id=user_id,
        order_id=order.id,
        status=PaymentStatus.SUCCESSFUL,
        amount=recalculated_total,
    )
    db.add(payment)
    await db.flush()

    payment_items = []
    for item in order.order_items:
        payment_item = PaymentItemModel(
            payment_id=payment.id,
            order_item_id=item.id,
            price_at_payment=item.price_at_order,
        )
        payment_items.append(payment_item)
    db.add_all(payment_items)

    order.status = OrderStatus.PAID
    await db.commit()

    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == order.id)
        .options(
            selectinload(OrderModel.order_items).selectinload(OrderItemModel.movie),
            selectinload(OrderModel.user).selectinload(UserModel.profile),
        )
    )
    return result.scalar_one()


async def get_all_orders(
    db: AsyncSession,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[OrderStatus] = None,
) -> list[OrderModel]:
    """
    Retrieves all orders, with optional filters (for admin).
    """
    query = select(OrderModel).options(
        selectinload(OrderModel.order_items)
        .selectinload(OrderItemModel.movie)
        .selectinload(MovieModel.genres),
        selectinload(OrderModel.user).selectinload(UserModel.profile),
    )
    if user_id:
        query = query.where(OrderModel.user_id == user_id)
    if status:
        query = query.where(OrderModel.status == status)
    if start_date:
        query = query.where(OrderModel.created_at >= start_date)
    if end_date:
        query = query.where(OrderModel.created_at <= end_date)

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_order_status(
    db: AsyncSession, order_id: int, new_status: OrderStatus
) -> OrderModel:
    """
    Updates the status of an order (for admin).
    Raises HTTPException if order not found.
    """
    order = await db.get(OrderModel, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )

    order.status = new_status
    await db.commit()
    await db.refresh(order)
    return order
