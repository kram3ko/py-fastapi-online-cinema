from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from database.models.base import Base
from database.models.accounts import UserModel
from database.models.movies import MovieModel


class Cart(Base):
    """
    Represents a user's shopping cart.
    Each user can have exactly one cart.
    """

    __tablename__ = "carts"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    user: Mapped[list["UserModel"]] = relationship(
        "UserModel", back_populates="cart"
    )
    items: Mapped[list["CartItem"]] = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Cart(id={self.id}, user_id={self.user_id})>"


class CartItem(Base):
    """
    Represents a single item (movie) placed in a user's cart.
    """

    __tablename__ = "cart_items"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = Column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = Column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    added_at: Mapped[datetime] = Column(
        DateTime, nullable=False, default=datetime.now(timezone.utc)
    )

    cart: Mapped[list["Cart"]] = relationship("Cart", back_populates="items")
    movie: Mapped[list["MovieModel"]] = relationship("MovieModel")

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id", name="uix_cart_movie"),
    )

    def __repr__(self):
        return f"<CartItem(id={self.id}, cart_id={self.cart_id}, movie_id={self.movie_id})>"
