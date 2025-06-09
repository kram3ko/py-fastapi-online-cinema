from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.movies import GenreModel, MovieModel, StarModel
from schemas.movies import (
    GenreCreateSchema,
    GenreUpdateSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    StarCreateSchema,
    StarUpdateSchema,
)


async def get_all_genres(db: AsyncSession) -> list[GenreModel]:
    """Retrieve all genres from the database, ordered by ID."""
    result = await db.execute(select(GenreModel).order_by(GenreModel.id))
    return result.scalars().all()


async def get_genre_by_id(db: AsyncSession, genre_id: int) -> GenreModel | None:
    """Retrieve a single genre by its ID."""
    result = await db.execute(select(GenreModel).where(GenreModel.id == genre_id))
    return result.scalar_one_or_none()


async def create_genre(db: AsyncSession, genre_data: GenreCreateSchema) -> GenreModel:
    """Create a new genre with the provided data."""
    genre = GenreModel(**genre_data.model_dump())
    db.add(genre)
    await db.commit()
    await db.refresh(genre)
    return genre


async def update_genre(db: AsyncSession, genre_id: int, genre_data: GenreUpdateSchema) -> GenreModel | None:
    """
    Update an existing genre with the provided data.
    Returns the updated genre or None if not found.
    """
    genre = await get_genre_by_id(db, genre_id)
    if not genre:
        return None

    for key, value in genre_data.model_dump(exclude_unset=True).items():
        setattr(genre, key, value)

    await db.commit()
    await db.refresh(genre)
    return genre


async def delete_genre(db: AsyncSession, genre_id: int) -> bool:
    """Delete a genre by its ID. Returns True if deleted, else False."""
    result = await db.execute(delete(GenreModel).where(GenreModel.id == genre_id))
    await db.commit()
    return result.rowcount > 0


async def get_all_stars(db: AsyncSession) -> list[StarModel]:
    """Retrieve all stars from the database, ordered by ID."""
    result = await db.execute(select(StarModel).order_by(StarModel.id))
    return result.scalars().all()


async def get_star_by_id(db: AsyncSession, star_id: int) -> StarModel | None:
    """Retrieve a single star by ID."""
    result = await db.execute(select(StarModel).where(StarModel.id == star_id))
    return result.scalar_one_or_none()


async def create_star(db: AsyncSession, star_data: StarCreateSchema) -> StarModel:
    """Create a new star with the provided data."""
    star = StarModel(**star_data.model_dump())
    db.add(star)
    await db.commit()
    await db.refresh(star)
    return star


async def update_star(db: AsyncSession, star_id: int, star_data: StarUpdateSchema) -> StarModel | None:
    """
    Update an existing star with the provided data.
    Returns the updated star or None if not found.
    """
    star = await get_star_by_id(db, star_id)
    if not star:
        return None

    for key, value in star_data.model_dump(exclude_unset=True).items():
        setattr(star, key, value)

    await db.commit()
    await db.refresh(star)
    return star


async def delete_star(db: AsyncSession, star_id: int) -> bool:
    """Delete a star by its ID. Returns True if deleted, else False."""
    result = await db.execute(delete(StarModel).where(StarModel.id == star_id))
    await db.commit()
    return result.rowcount > 0


async def get_all_movies(db: AsyncSession) -> list[MovieModel]:
    """Retrieve all movies from the database, ordered by ID."""
    result = await db.execute(select(MovieModel).order_by(MovieModel.id))
    return result.scalars().all()


async def get_movie_by_id(db: AsyncSession, movie_id: int) -> MovieModel | None:
    """
    Retrieve a single movie by ID including related genres, directors,
    stars, and certification.
    """
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
            selectinload(MovieModel.certification),
        )
        .where(MovieModel.id == movie_id)
    )
    return result.scalar_one_or_none()


async def create_movie(db: AsyncSession, movie_data: MovieCreateSchema) -> MovieModel:
    """
    Create a new movie including relationships to genres, stars, and directors.
    """
    movie = MovieModel(**movie_data.model_dump(exclude={"genre_ids", "star_ids", "director_ids"}))

    movie.genres = await db.execute(
        select(MovieModel.genres.property.mapper.class_).filter(
            MovieModel.genres.property.mapper.class_.id.in_(movie_data.genre_ids)
        )
    )
    movie.stars = await db.execute(
        select(MovieModel.stars.property.mapper.class_).filter(
            MovieModel.stars.property.mapper.class_.id.in_(movie_data.star_ids)
        )
    )
    movie.directors = await db.execute(
        select(MovieModel.directors.property.mapper.class_).filter(
            MovieModel.directors.property.mapper.class_.id.in_(movie_data.director_ids)
        )
    )

    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie


async def update_movie(db: AsyncSession, movie_id: int, data: MovieUpdateSchema) -> MovieModel | None:
    """
    Update a movie's details and optionally its related genres, stars, and directors.
    Returns the updated movie or None if not found.
    """
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        return None

    for key, value in data.model_dump(exclude_unset=True, exclude={"genre_ids", "star_ids", "director_ids"}).items():
        setattr(movie, key, value)

    if data.genre_ids:
        movie.genres = await db.execute(
            select(MovieModel.genres.property.mapper.class_).filter(
                MovieModel.genres.property.mapper.class_.id.in_(data.genre_ids)
            )
        )
    if data.star_ids:
        movie.stars = await db.execute(
            select(MovieModel.stars.property.mapper.class_).filter(
                MovieModel.stars.property.mapper.class_.id.in_(data.star_ids)
            )
        )
    if data.director_ids:
        movie.directors = await db.execute(
            select(MovieModel.directors.property.mapper.class_).filter(
                MovieModel.directors.property.mapper.class_.id.in_(data.director_ids)
            )
        )

    await db.commit()
    await db.refresh(movie)
    return movie


async def delete_movie(db: AsyncSession, movie_id: int) -> bool:
    """Delete a movie by its ID. Returns True if deleted, else False."""
    result = await db.execute(delete(MovieModel).where(MovieModel.id == movie_id))
    await db.commit()
    return result.rowcount > 0
