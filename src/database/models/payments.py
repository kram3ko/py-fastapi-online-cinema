from sqlalchemy import Column, Integer, ForeignKey, String, DECIMAL, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum as PyEnum
from database import Base

class PaymentStatus(PyEnum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.SUCCESSFUL, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    external_payment_id = Column(String, nullable=True)

    # (Опціонально) зв’язки:
    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments")

    def __repr__(self):
        return f"<Payment id={self.id}, user={self.user_id}, order={self.order_id}, status={self.status}>"