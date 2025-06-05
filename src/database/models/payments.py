from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, ForeignKey, String, DECIMAL, DateTime, Enum
from sqlalchemy.orm import relationship

from database import Base


class PaymentStatus(PyEnum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.SUCCESSFUL, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    external_payment_id = Column(String, nullable=True)

    user = relationship("UserModel", back_populates="payments")
    order = relationship("OrderModel", back_populates="payments")
    payment_items = relationship("PaymentItemModel", back_populates="payment")

    def __repr__(self):
        return f"<Payment id={self.id}, user={self.user_id}, order={self.order_id}, status={self.status}>"


class PaymentItemModel(Base):
    __tablename__ = "payment_items"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    price_at_payment = Column(DECIMAL(10, 2), nullable=False)

    payment = relationship("PaymentModel", back_populates="payment_items")
    order_item = relationship("OrderItemModel", back_populates="payment_items")
