from pydantic import BaseModel, condecimal, ConfigDict
from datetime import datetime
from typing import List, Optional


from database.models.orders import OrderStatus
from schemas.profiles import ProfileResponseSchema


class OrderItemResponse(BaseModel):
    id: int
    movie_id: int
    price_at_order: condecimal(max_digits=10, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    # The order is placed from the cart, so a list of movie IDs
    # might not be directly sent in the request body, but inferred from the user's cart.
    pass # not used, since order is created from cart, not manually


class OrderUpdateStatus(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatus
    total_amount: Optional[condecimal(max_digits=10, decimal_places=2)]
    order_items: List[OrderItemResponse] = []
    user: ProfileResponseSchema

    model_config = ConfigDict(from_attributes=True)


class OrderFilterParams(BaseModel):
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[OrderStatus] = None

    model_config = ConfigDict(from_attributes=True)
