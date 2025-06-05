from typing import Optional
from sqlalchemy import String, Text, DECIMAL, UniqueConstraint, ForeignKey, Table, Column, UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from database import Base
import uuid

MovieGenresModel = Table(
    "movie_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)

MovieDirectorsModel = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("director_id", ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True),
)

MovieStarsModel = Table(
    "movie_stars",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "star_id",
        ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieGenresModel,
        back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre(name='{self.name}')>"


class StarModel(Base):
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
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieDirectorsModel,
        back_populates="directors"
    )


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        back_populates="certification"
    )


class MovieModel(Base):
    __tablename__ = "movies"
    __table_args__ = (UniqueConstraint("name", "year", "time"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    imdb: Mapped[float] = mapped_column(nullable=True)
    votes: Mapped[int] = mapped_column(nullable=True)
    meta_score: Mapped[float | None] = mapped_column(nullable=False)
    gross: Mapped[float | None] = mapped_column(nullable=True)
    descriptions: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))

    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)
    certification: Mapped["CertificationModel"] = relationship("CertificationModel", back_populates="movies")

    genres: Mapped[list["GenreModel"]] = relationship(
        "GenreModel",
        secondary=MovieGenresModel,
        back_populates="movies"
    )

    stars: Mapped[list["StarModel"]] = relationship(
        "ActorModel",
        secondary=MovieStarsModel,
        back_populates="movies"
    )

    directors: Mapped[list["DirectorModel"]] = relationship(
        "DirectorModel",
        secondary=MovieDirectorsModel,
        back_populates="movies"
    )
