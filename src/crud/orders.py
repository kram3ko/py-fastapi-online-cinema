from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func

from database.models.accounts import UserModel
from database.models.movies import MovieModel
from database.models.orders import OrderItemModel, OrderModel, OrderStatus
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatus
from database.models.shopping_cart import Cart, CartItem


async def create_order_from_cart(
    user_id: int, db: AsyncSession
) -> OrderModel:
    """
    Creates a new order for a user based on their current shopping cart.
    Handles movie availability, purchased movies, and pending orders.

    Raises:
        HTTPException: If the cart is empty, or if no valid movies can be added to the order.
    """
    # Retrieve the user's cart and its items
    cart_result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(joinedload(Cart.items).joinedload(CartItem.movie))
    )
    cart = cart_result.scalars().first()

    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")

    # Collect movie IDs from the cart for efficient lookups
    movie_ids_in_cart = {item.movie_id for item in cart.items}

    # Validation: Exclude already purchased movies
    # Get all PAID orders for the user and their order_items
    purchased_movie_ids_query = await db.execute(
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(OrderModel.user_id == user_id, OrderModel.status == OrderStatus.PAID)
    )
    purchased_movie_ids = {item[0] for item in purchased_movie_ids_query.scalars().all()}

    # Validation: Check if there are other "pending" orders with the same movies
    # This prevents duplicate orders for the same movies if a pending order already exists.
    pending_movie_ids_in_other_orders_query = await db.execute(
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(OrderModel.user_id == user_id, OrderModel.status == OrderStatus.PENDING)
    )
    pending_movie_ids_in_other_orders = {item[0] for item in pending_movie_ids_in_other_orders_query.scalars().all()}

    # Create a new order
    new_order = OrderModel(user_id=user_id, status=OrderStatus.PENDING)
    db.add(new_order)
    await db.flush()  # To get new_order.id before adding order items

    total_amount = 0.0
    order_items_to_add = []
    excluded_movies_details = []  # To provide detailed feedback to the user/logs

    for cart_item in cart.items:
        movie = cart_item.movie
        movie_id = movie.id

        if movie_id in purchased_movie_ids:
            excluded_movies_details.append(
                {"movie_id": movie_id, "title": movie.name, "reason": "Already purchased"}
            )
            continue
        if movie_id in pending_movie_ids_in_other_orders:
            excluded_movies_details.append(
                {
                    "movie_id": movie_id,
                    "title": movie.name,
                    "reason": "Already in a pending order"
                }
            )
            continue

        order_item = OrderItemModel(
            order_id=new_order.id,
            movie_id=movie.id,
            price_at_order=movie.price
        )
        order_items_to_add.append(order_item)
        total_amount += float(movie.price)

    if not order_items_to_add:
        await db.rollback()  # Rollback the creation of an empty order
        detail_msg = "No valid movies to add to order."
        if excluded_movies_details:
            detail_msg += f" Excluded: {excluded_movies_details}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail_msg)

    db.add_all(order_items_to_add)
    new_order.total_amount = total_amount
    await db.commit()
    await db.refresh(new_order)  # Refresh to get the latest state including total_amount

    # Clear the shopping cart after successful order creation
    for item in cart.items:
        if item.movie_id in movie_ids_in_cart:  # Ensure we only delete items that were in the cart
            await db.delete(item)
    await db.commit()  # Save the cart clearing changes

    if excluded_movies_details:
        print(f"Warning: Some movies were excluded from the order: {excluded_movies_details}")
        # You might want to log this or return it as part of a more complex response

    return new_order


async def get_user_orders(user_id: int, db: AsyncSession) -> list[OrderModel]:
    """
    Retrieves all orders for a specific user, with loaded related data.
    """
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.user_id == user_id)
        .options(
            joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie),
            joinedload(OrderModel.user).joinedload(UserModel.profile),
        )
        .order_by(OrderModel.created_at.desc())
    )
    return list(result.scalars().all())


async def get_order_detail(db: AsyncSession, order_id: int, user_id: int) -> OrderModel:
    """
    Retrieves a specific order by its ID, ensuring the user has access.
    Raises HTTPException if order not found or user unauthorized.
    """
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == order_id, OrderModel.user_id == user_id)
        .options(
            joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie),
            joinedload(OrderModel.user).joinedload(UserModel.profile),
        )
    )
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or access denied.")
    return order


async def cancel_order(db: AsyncSession, order_id: int, user_id: int) -> OrderModel:
    """
    Cancels an order (updates its status to CANCELED).
    Raises HTTPException if order not found, already paid/canceled.
    """
    order = await get_order_detail(db, order_id, user_id)  # Reuse function for fetching and access check

    if order.status == OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid orders can only be canceled via refund request."
        )
    elif order.status == OrderStatus.CANCELED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already canceled.")

    order.status = OrderStatus.CANCELED
    await db.commit()
    await db.refresh(order)
    return order


async def process_order_payment(db: AsyncSession, order_id: int, user_id: int) -> OrderModel:
    """
    Processes payment for an order.
    Revalidates total amount, simulates payment, and updates order status to PAID.

    Raises:
        HTTPException: If the order is already paid, canceled, or a movie is unavailable.
    """
    order = await get_order_detail(db, order_id, user_id)

    if order.status == OrderStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order already paid.")
    if order.status == OrderStatus.CANCELED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot pay for a canceled order.")

    # Re-validate total amount before processing payment
    recalculated_total = 0.0
    for item in order.order_items:
        # Load the current price of the movie
        movie = await db.get(MovieModel, item.movie_id)
        if not movie or not movie.price:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Movie with ID {item.movie_id} in "
                                       f"order is no longer available or has no price.")

        # Use the current movie price for recalculation
        recalculated_total += float(movie.price)

    # Check if the total amount has significantly changed
    # Allow a small tolerance for floating-point inaccuracies
    if order.total_amount is None or abs(float(order.total_amount) - recalculated_total) > 0.01:
        order.total_amount = recalculated_total
        # In a real scenario, you might want to inform the user about price changes
        # and ask for re-confirmation before proceeding with payment.
        print(f"Warning: Order {order_id} total amount "
              f"re-calculated from {order.total_amount} to {recalculated_total}.")

    # Simulate payment processing
    # this would involve integrating with a payment gateway (Stripe).
    # If the payment is successful:
    new_payment = PaymentModel(
        user_id=user_id,
        order_id=order_id,
        amount=recalculated_total,  # Use the recalculated total amount
        status=PaymentStatus.SUCCESSFUL,
        external_payment_id="mock_payment_id_" + str(datetime.now().timestamp())  # Placeholder ID
    )
    db.add(new_payment)
    await db.flush()  # Get the payment ID before adding payment items

    # Add PaymentItemModel for each OrderItemModel
    payment_items_to_add = []
    for order_item in order.order_items:
        movie = await db.get(MovieModel, order_item.movie_id)  # Get movie again for price at payment
        if not movie:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Movie {order_item.movie_id} disappeared "
                                       f"during payment processing.")

        payment_item = PaymentItemModel(
            payment_id=new_payment.id,
            order_item_id=order_item.id,
            price_at_payment=movie.price  # Price of the movie at the time of payment
        )
        payment_items_to_add.append(payment_item)
    db.add_all(payment_items_to_add)

    order.status = OrderStatus.PAID  # Mark the order as paid
    await db.commit()  # Commit all changes: payment, payment items, order status update
    await db.refresh(order)

    return order


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
        joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie),
        joinedload(OrderModel.user).joinedload(UserModel.profile),
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    order.status = new_status
    await db.commit()
    await db.refresh(order)
    return order


