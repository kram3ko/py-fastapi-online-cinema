from pydantic import BaseModel, condecimal, ConfigDict
from datetime import datetime
from typing import List, Optional

from database.models.orders import OrderStatus
from schemas.profiles import ProfileResponseSchema
from schemas.movies import MovieListItemSchema


class OrderItemResponse(BaseModel):
    """
    Pydantic schema for responding with a single order item.
    Includes details about the movie associated with the item.
    """
    id: int
    movie_id: int
    price_at_order: condecimal(max_digits=10, decimal_places=2)
    movie: MovieListItemSchema # Movie details loaded with the order item

    model_config = ConfigDict(from_attributes=True)


class OrderUpdateStatus(BaseModel):
    """
    Pydantic schema for updating the status of an order.
    Typically used by administrative functions.
    """
    status: OrderStatus


class OrderResponse(BaseModel):
    """
    Pydantic schema for responding with full order details.
    Includes associated order items and user profile information.
    """
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatus
    total_amount: Optional[condecimal(max_digits=10, decimal_places=2)]
    order_items: List[OrderItemResponse] = [] # List of items included in the order
    user: ProfileResponseSchema # User profile details for the order owner

    model_config = ConfigDict(from_attributes=True)


class OrderFilterParams(BaseModel):
    """
    Pydantic schema for filtering orders.
    Used for query parameters in API endpoints, especially for admin views.
    """
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[OrderStatus] = None

    model_config = ConfigDict(from_attributes=True)


class OrderPaymentRequest(BaseModel):
    """
    Pydantic schema for requesting payment for an order.
    Currently empty as the order ID is passed in the URL,
    but can be extended to include payment gateway specific data.
    """
    pass