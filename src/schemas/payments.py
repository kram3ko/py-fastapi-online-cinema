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
    SUCCESSFUL = "SUCCESSFUL"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"


class PaymentCreateSchema(BaseModel):
    order_id: int
    amount: Decimal


class PaymentUpdateSchema(BaseModel):
    status: Optional[PaymentStatusSchema] = None
    external_payment_id: Optional[str] = None
    amount: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentBaseSchema(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatusSchema
    amount: Decimal
    external_payment_id: Optional[str] = None
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
