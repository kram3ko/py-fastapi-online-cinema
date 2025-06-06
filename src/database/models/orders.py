import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Enum,
    DECIMAL
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.functions import func

from database import Base


class OrderStatus(enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    CANCELED = "Canceled"


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[OrderStatus] = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    total_amount: Mapped[int] = Column(DECIMAL(10, 2), nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = Column(Integer, ForeignKey("orders.id"), nullable=False)
    movie_id: Mapped[int] = Column(Integer, ForeignKey("movies.id"), nullable=False)
    price_at_order: Mapped[DECIMAL] = Column(DECIMAL(10, 2), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="order_items")
