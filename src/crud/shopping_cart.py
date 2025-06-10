from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.movies import MovieModel
from database.models.orders import OrderItemModel, OrderModel, OrderStatus
from database.models.shopping_cart import Cart, CartItem


class CartError(Exception):
    """Base exception for cart-related errors."""

    pass


class MovieNotFoundError(CartError):
    """Raised when movie doesn't exist."""

    pass


class MovieAlreadyInCartError(CartError):
    """Raised when movie is already in cart."""

    pass


class MovieAlreadyPurchasedError(CartError):
    """Raised when movie was already purchased by user."""

    pass


class CartNotFoundError(CartError):
    """Raised when cart doesn't exist."""

    pass


class MovieNotInCartError(CartError):
    """Raised when trying to remove a movie that's not in the cart."""

    pass


async def get_user_cart(db: AsyncSession, user_id: int) -> Optional[Cart]:
    """
    Get user's shopping cart with all items.
    If cart doesn't exist, returns None.
    """
    query = (
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(MovieModel.genres)
        )
        .where(Cart.user_id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_cart(db: AsyncSession, user_id: int) -> Cart:
    """Create a new cart for user."""
    cart = Cart(user_id=user_id)
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    return cart


async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
    """Get existing cart or create new one if it doesn't exist."""
    cart = await get_user_cart(db, user_id)
    if not cart:
        cart = await create_cart(db, user_id)
    return cart


async def is_movie_purchased(
    db: AsyncSession, user_id: int, movie_id: int
) -> bool:
    """
    Check if user has already purchased the movie.
    Returns True if movie was purchased, False otherwise.
    """
    query = (
        select(OrderItemModel)
        .join(OrderModel)
        .where(
            and_(
                OrderModel.user_id == user_id,
                OrderItemModel.movie_id == movie_id,
                OrderModel.status == OrderStatus.PAID,
            )
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def add_movie_to_cart(
    db: AsyncSession, cart_id: int, movie_id: int, user_id: int
) -> tuple[Optional[CartItem], Optional[CartError]]:
    """
    Add movie to cart.
    Returns a tuple of (cart_item, error).
    If successful, returns (cart_item, None).
    If error occurs, returns (None, error).
    """
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        return None, MovieNotFoundError()

    query = select(CartItem).where(
        CartItem.cart_id == cart_id, CartItem.movie_id == movie_id
    )
    result = await db.execute(query)
    if result.scalar_one_or_none():
        return None, MovieAlreadyInCartError()

    if await is_movie_purchased(db, user_id, movie_id):
        return None, MovieAlreadyPurchasedError()

    cart_item = CartItem(cart_id=cart_id, movie_id=movie_id)
    db.add(cart_item)
    await db.commit()

    query = (
        select(CartItem)
        .options(selectinload(CartItem.movie).selectinload(MovieModel.genres))
        .where(CartItem.id == cart_item.id)
    )
    result = await db.execute(query)
    cart_item = result.scalar_one()

    return cart_item, None


async def remove_movie_from_cart(
    db: AsyncSession, cart_id: int, movie_id: int
) -> tuple[bool, Optional[CartError]]:
    """
    Remove movie from cart.
    Returns a tuple of (success, error).
    If successful, returns (True, None).
    If error occurs, returns (False, error).
    """
    cart = await db.get(Cart, cart_id)
    if not cart:
        return False, CartNotFoundError()

    movie = await db.get(MovieModel, movie_id)
    if not movie:
        return False, MovieNotFoundError()

    query = select(CartItem).where(
        CartItem.cart_id == cart_id, CartItem.movie_id == movie_id
    )
    result = await db.execute(query)
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        return False, MovieNotInCartError()

    await db.delete(cart_item)
    await db.commit()
    return True, None


async def clear_cart(
    db: AsyncSession, cart_id: int
) -> tuple[bool, Optional[CartError]]:
    """
    Remove all items from cart.
    Returns a tuple of (success, error).
    If successful, returns (True, None).
    If error occurs, returns (False, error).
    """
    cart = await db.get(Cart, cart_id)
    if not cart:
        return False, CartNotFoundError()

    query = select(CartItem).where(CartItem.cart_id == cart_id)
    result = await db.execute(query)
    items = result.scalars().all()

    for item in items:
        await db.delete(item)

    await db.commit()
    return True, None
