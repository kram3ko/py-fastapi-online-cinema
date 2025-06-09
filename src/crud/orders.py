# import logging
# from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import func
# from typing import List, Tuple, Optional
# from decimal import Decimal
# from datetime import timedelta
#
# from src.database.models.orders import OrderModel, OrderItemModel, OrderStatus
# from src.database.models.accounts import UserModel
# from src.database.models.movies import MovieModel
# from src.database.models.shopping_cart import Cart, CartItem
#
# from src.schemas.orders import OrderFilterParams
#
# from src.exceptions.orders import (
#     CartEmptyError, MovieNotAvailableError, MovieAlreadyPurchasedError,
#     DuplicatePendingOrderError, OrderCancellationError, OrderNotFoundException,
#     UnauthorizedOrderAccess
# )
#
#
# logger = logging.getLogger(__name__) # Basic logger setup for potential debugging
#
#
# def get_user_cart_items_for_order(db: Session, user_id: int) -> List[CartItem]:
#     """
#     Retrieves all cart items for a given user, eagerly loading associated Movie data.
#     This function is crucial for creating an order from the cart.
#     """
#     cart = db.query(Cart).filter(Cart.user_id == user_id).first()
#     if not cart:
#         logger.warning(f"Cart not found for user_id: {user_id}")
#         return []
#
#     # Eagerly load the associated movie for each cart item to avoid N+1 queries later
#     return db.query(CartItem).filter(CartItem.cart_id == cart.id).options(joinedload(CartItem.movie)).all()
#
#
# def get_user_purchased_movie_ids(db: Session, user_id: int) -> List[int]:
#     """
#     Retrieves a list of movie IDs that the user has already purchased (status 'Paid').
#     Used to prevent re-ordering already owned movies.
#     """
#     purchased_movie_ids = (
#         db.query(OrderItemModel.movie_id)
#         .join(OrderModel)
#         .filter(OrderModel.user_id == user_id, OrderModel.status == OrderStatus.PAID)
#         .distinct()
#         .all()
#     )
#     return [movie_id for (movie_id,) in purchased_movie_ids]
#
#
# def create_order(db: Session, user_id: int) -> Tuple[OrderModel, List[str]]:
#     """
#     Places a new order for movies based on the user's current cart.
#     Handles validations: cart emptiness, movie availability, already purchased movies,
#     and duplicate pending orders.
#     Returns the created OrderModel object and a list of messages for movies that were excluded.
#     """
#     excluded_movie_messages: List[str] = []
#
#     cart_items = get_user_cart_items_for_order(db, user_id)
#
#     if not cart_items:
#         raise CartEmptyError("Cannot place an order with an empty cart.")
#
#     purchased_movie_ids = get_user_purchased_movie_ids(db, user_id)
#
#     final_movies_for_order: List[MovieModel] = []
#     initial_total_amount: Decimal = Decimal('0.00')
#
#     # Movies that will be removed from cart regardless of being ordered or excluded
#     movie_ids_to_remove_from_cart: List[int] = []
#
#     for cart_item in cart_items:
#         movie = cart_item.movie
#
#         # Data consistency check
#         if not movie:
#             excluded_movie_messages.append(f"Movie linked to cart item ID {cart_item.id} not found in database.")
#             movie_ids_to_remove_from_cart.append(cart_item.movie_id)
#             continue
#
#
#         # TODO: add check for is movie active [IF NECESSARY]
#
#
#         if movie.id in purchased_movie_ids:
#             excluded_movie_messages.append(f"Movie '{movie.name}' (ID: {movie.id}) has already been purchased by you.")
#             movie_ids_to_remove_from_cart.append(movie.id)
#             continue
#
#         final_movies_for_order.append(movie)
#         initial_total_amount += Decimal(str(movie.price))
#         movie_ids_to_remove_from_cart.append(movie.id)
#
#     if not final_movies_for_order:
#         # If all movies were excluded, the cart is effectively empty for order placement
#         raise CartEmptyError("No eligible movies found in your cart to place an order after validation.")
#
#     # Check for duplicate pending orders to prevent redundant orders
#     current_movie_ids_set = set(m.id for m in final_movies_for_order)
#     potential_duplicate_pending_orders = (
#         db.query(OrderModel)
#         .filter(OrderModel.user_id == user_id, OrderModel.status == OrderStatus.PENDING)
#         .options(joinedload(OrderModel.order_items))
#         .all()
#     )
#
#     for pending_order in potential_duplicate_pending_orders:
#         pending_movie_ids_set = set(item.movie_id for item in pending_order.order_items)
#         if pending_movie_ids_set == current_movie_ids_set:
#             raise DuplicatePendingOrderError(
#                 f"An order with the exact same set of movies (ID: {pending_order.id}) is already {OrderStatus.PENDING.value}. "
#                 "Please complete or cancel it before placing a new one."
#             )
#
#     order = OrderModel(
#         user_id=user_id,
#         status=OrderStatus.PENDING, # New orders start as PENDING
#         total_amount=initial_total_amount
#     )
#     db.add(order)
#     db.flush() # Flush to get the order.id before creating OrderItems
#
#     for movie in final_movies_for_order:
#         order_item = OrderItemModel(
#             order_id=order.id,
#             movie_id=movie.id,
#             price_at_order=Decimal(str(movie.price))
#         )
#         db.add(order_item)
#
#     user_cart = db.query(Cart).filter(Cart.user_id == user_id).first()
#     if user_cart and movie_ids_to_remove_from_cart:
#         db.query(CartItem).filter(
#             CartItem.cart_id == user_cart.id,
#             CartItem.movie_id.in_(movie_ids_to_remove_from_cart)
#         ).delete(synchronize_session=False) # Use synchronize_session=False for bulk deletes
#
#     db.commit()
#     db.refresh(order)
#
#     order_with_details = (
#         db.query(OrderModel)
#         .options(
#             joinedload(OrderModel.user),
#             joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie)
#         )
#         .filter(OrderModel.id == order.id)
#         .first()
#     )
#
#     return order_with_details, excluded_movie_messages
#
#
# def get_user_orders(db: Session, user_id: int) -> List[OrderModel]:
#     """
#     Retrieves all orders for a specific user, ordered by creation date (descending).
#     Includes eager loading of associated user, order items, and movie details.
#     """
#     return (
#         db.query(OrderModel)
#         .options(
#             joinedload(OrderModel.user),
#             joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie)
#         )
#         .filter(OrderModel.user_id == user_id)
#         .order_by(OrderModel.created_at.desc())
#         .all()
#     )
#
# def get_order_details(db: Session, order_id: int, user_id: int) -> Optional[OrderModel]:
#     """
#     Retrieves a single order by its ID for a specific user.
#     Ensures that the requested order belongs to the specified user to prevent unauthorized access.
#     """
#     order = (
#         db.query(OrderModel)
#         .options(
#             joinedload(OrderModel.user),
#             joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie)
#         )
#         .filter(OrderModel.id == order_id)
#         .first()
#     )
#     if not order:
#         raise OrderNotFoundException(order_id)
#     if order.user_id != user_id:
#         raise UnauthorizedOrderAccess()
#     return order
#
#
# def cancel_order(db: Session, order_id: int, user_id: int) -> OrderModel:
#     """
#     Allows a user to cancel their own pending order.
#     Checks if the order exists, belongs to the user, and is in a cancellable state (e.g., PENDING).
#     """
#     order = db.query(OrderModel).filter(OrderModel.id == order_id, OrderModel.user_id == user_id).first()
#     if not order:
#         raise OrderNotFoundException(order_id)
#
#     if order.status == OrderStatus.PAID: # Cannot cancel if already paid
#         raise OrderCancellationError("Paid orders cannot be cancelled directly.")
#     elif order.status == OrderStatus.CANCELED:
#         raise OrderCancellationError("Order is already canceled.")
#
#     order.status = OrderStatus.CANCELED
#     db.add(order)
#     db.commit()
#     db.refresh(order)
#     return order
#
#
# def update_order_status(db: Session, order_id: int, new_status: OrderStatus) -> OrderModel:
#     """
#     Updates the status of an order to a new specified status.
#     Typically used for internal processes (e.g., by an admin or payment gateway callback).
#     """
#     order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
#     if not order:
#         raise OrderNotFoundException(order_id)
#
#     order.status = new_status
#     db.add(order)
#     db.commit()
#     db.refresh(order)
#

##############################################################################################################




from typing import List, Optional
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException, status

from database.models.orders import OrderModel, OrderItemModel, OrderStatus
from database.models.shopping_cart import CartItem, Cart
from database.models.movies import MovieModel
from database.models.accounts import UserModel

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
