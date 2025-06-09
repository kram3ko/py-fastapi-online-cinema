from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CartItemBase(BaseModel):
    movie_id: int


class CartItemCreate(CartItemBase):
    pass


class CartItemResponse(CartItemBase):
    id: int
    cart_id: int
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartBase(BaseModel):
    user_id: int


class CartCreate(CartBase):
    pass


class CartResponse(CartBase):
    id: int
    items: list[CartItemResponse]

    model_config = ConfigDict(from_attributes=True)


class CartUpdate(BaseModel):
    items: list[CartItemCreate]
