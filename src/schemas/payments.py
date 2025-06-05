from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import List, Optional


class PaymentItemBase(BaseModel):
    id: int
    order_item_id: int
    price_at_payment: Decimal

    class Config:
        orm_mode = True


class PaymentStatus(str, Enum):
    successful = "successful"
    canceled = "canceled"
    refunded = "refunded"


class PaymentCreate(BaseModel):
    order_id: int
    amount: Decimal


class PaymentBase(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatus
    amount: Decimal
    external_payment_id: Optional[str] = None
    payment_items: List[PaymentItemBase] = []

    class Config:
        orm_mode = True


class PaymentList(BaseModel):
    payments: List[PaymentBase]
