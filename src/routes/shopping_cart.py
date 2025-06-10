from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.dependencies import get_current_user
from crud import shopping_cart as cart_crud
from crud.shopping_cart import (
    CartNotFoundError,
    MovieAlreadyInCartError,
    MovieAlreadyPurchasedError,
    MovieNotFoundError,
    MovieNotInCartError,
)
from database.deps import get_db
from database.models.accounts import UserModel
from schemas.accounts import MessageResponseSchema
from schemas.shopping_cart import (
    CartItemCreate,
    CartItemResponse,
    CartResponse,
)

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
    cart_item, error = await cart_crud.add_movie_to_cart(db, cart.id, item.movie_id, current_user.id)

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
    success, error = await cart_crud.remove_movie_from_cart(db, cart.id, movie_id)

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
