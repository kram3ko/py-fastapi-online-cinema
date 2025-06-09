from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.dependencies import get_current_user
from crud import shopping_cart as cart_crud
from database.deps import get_db
from database.models.accounts import UserModel
from schemas.accounts import MessageResponseSchema
from schemas.shopping_cart import (
    CartItemCreate,
    CartItemResponse,
    CartResponse,
)
from security.http import jwt_security

router = APIRouter(dependencies=[Depends(get_current_user), Depends(jwt_security)])


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
    cart_item = await cart_crud.add_movie_to_cart(db, cart.id, item.movie_id, current_user.id)

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is already in cart, doesn't exist, or was already purchased",
        )

    return cart_item


@router.delete("/items/{movie_id}", response_model=MessageResponseSchema)
async def remove_movie_from_cart(
    movie_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    """Remove movie from cart."""
    cart = await cart_crud.get_user_cart(db, current_user.id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    removed = await cart_crud.remove_movie_from_cart(db, cart.id, movie_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in cart",
        )

    return MessageResponseSchema(message="Movie removed from cart")


@router.delete("/", response_model=MessageResponseSchema)
async def clear_cart(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    """Clear all items from cart."""
    cart = await cart_crud.get_user_cart(db, current_user.id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cleared = await cart_crud.clear_cart(db, cart.id)
    if not cleared:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    return MessageResponseSchema(message="Cart cleared successfully")
