from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import List, Optional


class PaymentItemBaseSchema(BaseModel):
    id: int
    order_item_id: int
    price_at_payment: Decimal

    class Config:
        orm_mode = True


class PaymentStatusSchema(str, Enum):
    successful = "successful"
    canceled = "canceled"
    refunded = "refunded"


class PaymentCreateSchema(BaseModel):
    order_id: int
    amount: Decimal


class PaymentBaseSchema(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatusSchema
    amount: Decimal
    external_payment_id: Optional[str] = None
    payment_items: List[PaymentItemBaseSchema] = []

    class Config:
        orm_mode = True


class PaymentListSchema(BaseModel):
    payments: List[PaymentBaseSchema]
