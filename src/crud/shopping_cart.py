from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.movies import MovieModel
from database.models.orders import OrderItemModel, OrderModel, OrderStatus
from database.models.shopping_cart import Cart, CartItem


async def get_user_cart(db: AsyncSession, user_id: int) -> Optional[Cart]:
    """
    Get user's shopping cart with all items.
    If cart doesn't exist, returns None.
    """
    query = select(Cart).options(selectinload(Cart.items).selectinload(CartItem.movie)).where(Cart.user_id == user_id)
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


async def is_movie_purchased(db: AsyncSession, user_id: int, movie_id: int) -> bool:
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


async def add_movie_to_cart(db: AsyncSession, cart_id: int, movie_id: int, user_id: int) -> Optional[CartItem]:
    """
    Add movie to cart.
    Returns None if:
    - movie is already in cart
    - movie doesn't exist
    - movie was already purchased by user
    """

    movie = await db.get(MovieModel, movie_id)
    if not movie:
        return None

    query = select(CartItem).where(CartItem.cart_id == cart_id, CartItem.movie_id == movie_id)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        return None

    if await is_movie_purchased(db, user_id, movie_id):
        return None

    cart_item = CartItem(cart_id=cart_id, movie_id=movie_id)
    db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)
    return cart_item


async def remove_movie_from_cart(db: AsyncSession, cart_id: int, movie_id: int) -> bool:
    """
    Remove movie from cart.
    Returns True if movie was removed, False if it wasn't in cart.
    """
    query = select(CartItem).where(CartItem.cart_id == cart_id, CartItem.movie_id == movie_id)
    result = await db.execute(query)
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        return False

    await db.delete(cart_item)
    await db.commit()
    return True


async def clear_cart(db: AsyncSession, cart_id: int) -> bool:
    """
    Remove all items from cart.
    Returns True if cart was cleared, False if cart doesn't exist.
    """
    cart = await db.get(Cart, cart_id)
    if not cart:
        return False

    query = select(CartItem).where(CartItem.cart_id == cart_id)
    result = await db.execute(query)
    items = result.scalars().all()

    for item in items:
        await db.delete(item)

    await db.commit()
    return True
