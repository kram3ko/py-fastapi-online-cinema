from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class PaymentStatusEnum(str, Enum):
    successful = "successful"
    canceled = "canceled"
    refunded = "refunded"


class AdminPaymentFilterSchema(BaseModel):
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    status: Optional[PaymentStatusEnum] = Field(None, description="Filter by payment status")
    date_from: Optional[datetime] = Field(None, description="Start date for filtering")
    date_to: Optional[datetime] = Field(None, description="End date for filtering")
