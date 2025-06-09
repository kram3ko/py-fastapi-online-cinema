from typing import List, Optional
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from database.models.orders import OrderModel, OrderItemModel, OrderStatus

from crud.shopping_cart import get_user_cart, clear_cart
from exceptions.orders import (
    EmptyCartException,
    UnavailableMovieException
)


async def create_order_from_cart(user_id: int, db: AsyncSession) -> OrderModel:
    """
    Core logic: fetch cart, validate, create order, clear cart.
    """
    # Get user's cart
    cart = await get_user_cart(db, user_id)
    if not cart or not cart.items:
        raise EmptyCartException()

    cart_items = cart.items

    # Get list of already purchased movie IDs
    query = (
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(OrderModel.user_id == user_id, OrderModel.status == OrderStatus.PAID)
    )
    result = await db.execute(query)
    purchased_ids = {row[0] for row in result.all()}

    # Filter valid items
    valid_items: list[tuple[int, Decimal]] = []
    total = Decimal("0.00")

    for item in cart_items:
        movie = item.movie
        if not movie:
            continue  # skip deleted
        if movie.id in purchased_ids:
            continue  # already bought
        valid_items.append((movie.id, movie.price))
        total += movie.price

    if not valid_items:
        raise UnavailableMovieException()

    # Create Order
    order = OrderModel(user_id=user_id, total_amount=total)
    db.add(order)
    await db.flush()  # generates order.id

    # Create OrderItems
    order_items = [
        OrderItemModel(order_id=order.id, movie_id=movie_id, price_at_order=price)
        for movie_id, price in valid_items
    ]
    db.add_all(order_items)

    # Save and clear cart
    await db.commit()
    await clear_cart(db, cart.id)
    await db.refresh(order)

    return order


async def get_user_orders(user_id: int, db: AsyncSession) -> List[OrderModel]:
    """
    List all orders of a user.
    """
    query = (
        select(OrderModel)
        .options(selectinload(OrderModel.order_items))
        .where(OrderModel.user_id == user_id)
        .order_by(OrderModel.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_orders(
    db: AsyncSession,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[OrderStatus] = None,
) -> List[OrderModel]:
    """
    Admin filtering support.
    """
    query = select(OrderModel).options(selectinload(OrderModel.order_items), selectinload(OrderModel.user))

    if user_id:
        query = query.where(OrderModel.user_id == user_id)
    if status:
        query = query.where(OrderModel.status == status)
    if start_date:
        query = query.where(OrderModel.created_at >= start_date)
    if end_date:
        query = query.where(OrderModel.created_at <= end_date)

    query = query.order_by(OrderModel.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


async def get_order_detail(
    db: AsyncSession, order_id: int, user_id: int
) -> OrderModel:
    query = (
        select(OrderModel)
        .options(selectinload(OrderModel.order_items))
        .where(OrderModel.id == order_id, OrderModel.user_id == user_id)
    )
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


async def cancel_order(
    db: AsyncSession, order_id: int, user_id: int
) -> OrderModel:
    order = await db.get(OrderModel, order_id)
    if not order or order.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be canceled"
        )

    order.status = OrderStatus.CANCELED
    await db.commit()
    await db.refresh(order)
    return order



async def update_order_status(
    db: AsyncSession, order_id: int, new_status: OrderStatus
) -> Optional[OrderModel]:
    """
    Manual status update support (e.g. for refunds/cancellation).
    """
    order = await db.get(OrderModel, order_id)
    if not order:
        return None

    order.status = new_status
    await db.commit()
    await db.refresh(order)
    return order
