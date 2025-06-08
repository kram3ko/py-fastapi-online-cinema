from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from database.models.accounts import UserModel
from database.models.orders import OrderStatus


class OrderItemResponse(BaseModel):
    id: int
    movie_id: int
    price_at_order: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    user_id: int
    movie_id: int
    price: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=10, decimal_places=2)
    status: str


class OrderCreate(OrderBase):
    # The order is placed from the cart, so a list of movie IDs
    # might not be directly sent in the request body, but inferred from the user's cart.
    # Empty body for 'place order from my cart' scenario
    pass


class OrderUpdate(BaseModel):
    price: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    status: Optional[str] = None


class OrderUpdateStatus(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatus
    total_amount: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    order_items: list[OrderItemResponse] = []
    user: UserModel

    model_config = ConfigDict(from_attributes=True)


class OrderFilterParams(BaseModel):
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[OrderStatus] = None

    model_config = ConfigDict(from_attributes=True)
