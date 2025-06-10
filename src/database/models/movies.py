import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DECIMAL, Column, DateTime, ForeignKey, String, Table, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base

if TYPE_CHECKING:
    from database.models.accounts import UserModel
    from database.models.orders import OrderItemModel


MovieGenresModel = Table(
    "movie_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
)
""" Association table linking movies and genres (many_to_many)."""

MovieDirectorsModel = Table(
    "movie_directors",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "director_id",
        ForeignKey("directors.id", ondelete="CASCADE"),
        primary_key=True
    ),
)
""" Association table linking movies and directors (many_to_many)."""

MovieStarsModel = Table(
    "movie_stars",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
    Column(
        "star_id",
        ForeignKey("stars.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
)
""" Association table linking movies and stars (many_to_many)."""


class GenreModel(Base):
    """
    Genre of a movie (e.g. Action, Comedy).

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the genre.
        movies (list[MovieModel]): Movies associated with this genre.
    """

    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", secondary=MovieGenresModel, back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre(name='{self.name}')>"


class StarModel(Base):
    """
    Actor or actress featured in a movie.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the star.
        movies (list[MovieModel]): Movies this star appears in.
    """

    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieStarsModel,
        back_populates="stars"
    )

    def __repr__(self):
        return f"<Star(name='{self.name}')>"


class DirectorModel(Base):
    """
    Director of a movie.

    Attributes:
        id (int): Primary key.
        name (Optional[str]): Unique name of the director.
        movies (list[MovieModel]): Movies directed by this person.
    """

    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", secondary=MovieDirectorsModel, back_populates="directors"
    )


class CertificationModel(Base):
    """
    Certification of a movie.

    Attributes:
        id (int): Primary key.
        name (str): Certification label.
        movies (list[MovieModel]): Movies with this certification.
    """

    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        back_populates="certification"
    )


class MovieModel(Base):
    """
    Main model representing a movie.

    Attributes:
        id (int): Primary key.
        uuid_movie (UUID): Unique identifier.
        name (str): Movie title.
        year (int): Release year.
        time (int): Duration in minutes.
        imdb (float): IMDb rating.
        votes (int | None): Number of IMDb votes.
        meta_score (float): Metacritic score.
        gross (float | None): Box office gross.
        descriptions (str): Movie descriptions.
        price (float): Rental or purchase price.

        certification_id (int): Foreign key to the CertificationModel.
        certification (CertificationModel): Linked certification.

        genres (list[GenreModel]): Genres this movie belongs to.
        stars (list[StarModel]): Stars features in the movie.
        directors (list[DirectorModel]): Directors of the movie.
    """

    __tablename__ = "movies"
    __table_args__ = (UniqueConstraint("name", "year", "time"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid_movie: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    imdb: Mapped[float] = mapped_column(nullable=True)
    votes: Mapped[int] = mapped_column(nullable=True)
    meta_score: Mapped[float | None] = mapped_column(nullable=True)
    gross: Mapped[float | None] = mapped_column(nullable=True)
    descriptions: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id"),
        nullable=False
    )
    certification: Mapped["CertificationModel"] = relationship(
        "CertificationModel",
        back_populates="movies"
    )

    genres: Mapped[list["GenreModel"]] = relationship(
        "GenreModel",
        secondary=MovieGenresModel,
        back_populates="movies"
    )

    stars: Mapped[list["StarModel"]] = relationship(
        "StarModel",
        secondary=MovieStarsModel,
        back_populates="movies"
    )

    directors: Mapped[list["DirectorModel"]] = relationship(
        "DirectorModel",
        secondary=MovieDirectorsModel,
        back_populates="movies"
    )
    order_items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="movie"
    )
    likes: Mapped[list["MovieLikeModel"]] = relationship(
        "MovieLikeModel",
        back_populates="movies",
        cascade="all, delete-orphan"
    )
    comments: Mapped[list["CommentModel"]] = relationship(
        back_populates="movies",
        cascade="all, delete-orphan"
    )
    # favorited_by: Mapped[list["FavoriteMovieModel"]] = relationship(
    #     back_populates="movies",
    # )


class MovieLikeModel(Base):
    __tablename__ = "movie_likes"
    __table_args__ = (
        UniqueConstraint("movie_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id",
        ondelete="CASCADE")
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id",
        ondelete="CASCADE")
    )
    is_like: Mapped[bool] = mapped_column(nullable=False)

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="movie_likes"
    )
    movies: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="likes"
    )


class CommentModel(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True
    )
    content: Mapped[str] = mapped_column(nullable=False)
    rating: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"),
        nullable=False
    )

    user: Mapped["UserModel"] = relationship(
        back_populates="comments"
    )
    movies: Mapped["MovieModel"] = relationship(
        back_populates="comments"
    )


# class FavoriteMovieModel(Base):
#     __tablename__ = "favorite_movies"
#     __table_args__ = (
#         UniqueConstraint("user_id", "movie_id"),
#     )
#
#     id: Mapped[int] = mapped_column(primary_key=True, index=True)
#     user_id: Mapped[int] = mapped_column(
#         ForeignKey("users.id", ondelete="CASCADE"),
#         nullable=False
#     )
#     movie_id: Mapped[int] = mapped_column(
#         ForeignKey("movies.id", ondelete="CASCADE"),
#         nullable=False
#     )
#
#     user: Mapped["UserModel"] = relationship(
#         back_populates="favorite_movies"
#     )
#     movies: Mapped["MovieModel"] = relationship(
#         back_populates="favorited_by"
#     )
