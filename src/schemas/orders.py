from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from database.models.orders import OrderStatus
from schemas.movies import MovieListItemSchema
from schemas.profiles import ProfileResponseSchema


class OrderMovieSchema(BaseModel):
    """
    Simplified movie schema for order items that doesn't require genres.
    """
    id: int
    name: str
    year: int
    imdb: Optional[float]
    time: int
    price: float

    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    """
    Pydantic schema for responding with a single order item.
    Includes details about the movie associated with the item.
    """
    id: int
    movie_id: int
    price_at_order: Decimal = Field(..., max_digits=10, decimal_places=2)
    movie: OrderMovieSchema  # Movie details loaded with the order item

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
    total_amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    order_items: list[OrderItemResponse] = []  # List of items included in the order
    user: ProfileResponseSchema  # User profile details for the order owner

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
    Currently empty as the order ID is passed in the URL
    but can be extended to include payment gateway specific data.
    """
    pass
