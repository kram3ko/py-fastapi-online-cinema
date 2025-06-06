import enum
from datetime import datetime

from sqlalchemy import DECIMAL, Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql.functions import func

from database.models.accounts import UserModel
from database.models.base import Base
from database.models.movies import MovieModel


class OrderStatus(enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    CANCELED = "Canceled"


class OrderModel(Base):
    __tablename__ = "orders"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[OrderStatus] = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    total_amount: Mapped[int] = Column(DECIMAL(10, 2), nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")
    order_items: Mapped[list["OrderItemModel"]] = relationship("OrderItemModel", back_populates="order")


class OrderItemModel(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = Column(Integer, ForeignKey("orders.id"), nullable=False)
    movie_id: Mapped[int] = Column(Integer, ForeignKey("movies.id"), nullable=False)
    price_at_order: Mapped[DECIMAL] = Column(DECIMAL(10, 2), nullable=False)

    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="order_items")
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="order_items")
