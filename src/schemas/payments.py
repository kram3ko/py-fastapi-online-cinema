from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PaymentItemBaseSchema(BaseModel):
    id: int
    order_item_id: int
    price_at_payment: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentStatusSchema(str, Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"
    EXPIRED = "EXPIRED"


class PaymentCreateSchema(BaseModel):
    order_id: int


class CheckoutSessionResponse(BaseModel):
    payment_url: str
    payment_id: int
    session_id: str

    model_config = ConfigDict(from_attributes=True)


class PaymentUpdateSchema(BaseModel):
    status: Optional[PaymentStatusSchema] = None
    session_id: Optional[str] = None
    amount: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentBaseSchema(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatusSchema
    amount: Decimal
    session_id: Optional[str] = None
    payment_intent_id: Optional[str] = None
    payment_items: list[PaymentItemBaseSchema] = []

    model_config = ConfigDict(from_attributes=True)


class PaymentListSchema(BaseModel):
    payments: list[PaymentBaseSchema]
    total: int
    skip: int
    limit: int


class AdminPaymentFilter(BaseModel):
    user_id: Optional[int] = None
    status: Optional[PaymentStatusSchema] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 10


class WebhookResponse(BaseModel):
    status: str
    message: str
    event_type: str
    payment_id: str


class PaymentStatisticsResponse(BaseModel):
    total_amount: Decimal
    total_payments: int
    successful_payments: int
    refunded_payments: int
    success_rate: float


class RefundResponse(BaseModel):
    payment_id: int
    order_id: int
    status: str = "refunded"
