from fastapi import HTTPException, params
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from database.models.movies import CertificationModel, DirectorModel, GenreModel, MovieModel, StarModel, \
    MovieGenresModel
from pagination import Page, Params
from schemas.movies import (
    CertificationCreateSchema,
    CertificationUpdateSchema,
    DirectorCreateSchema,
    GenreCreateSchema,
    GenreUpdateSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    StarCreateSchema,
    StarUpdateSchema, GenreReadSchema,
)


async def get_all_genres(
        db: AsyncSession
) -> list[GenreModel]:
    """Retrieve all genres from the database, ordered by ID."""
    stmt = (
        select(
            GenreModel.id,
            GenreModel.name,
            func.count(MovieGenresModel.c.movie_id).label("movie_count")
        )
        .join(MovieGenresModel, GenreModel.id == MovieGenresModel.c.genre_id)
        .group_by(GenreModel.id)
        .order_by(func.count(MovieGenresModel.c.movie_id).desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [GenreReadSchema(id=row.id, name=row.name, movie_count=row.movie_count) for row in rows]


async def get_genre_by_id(
        db: AsyncSession,
        genre_id: int
) -> GenreModel | None:
    """Retrieve a single genre by its ID."""
    result = await db.execute(
        select(GenreModel)
        .where(GenreModel.id == genre_id)
    )
    return result.scalar_one_or_none()


async def add_genre(
        db: AsyncSession,
        genre_data: GenreCreateSchema
) -> GenreModel:
    """Create a new genre with the provided data."""
    genre = GenreModel(**genre_data.model_dump())
    db.add(genre)
    await db.commit()
    await db.refresh(genre)
    return genre


async def edit_genre(
        db: AsyncSession,
        genre_id: int,
        genre_data: GenreUpdateSchema
) -> GenreModel | None:
    """
    Update an existing genre with the provided data.
    Returns the updated genre or None if not found.
    """
    genre = await get_genre_by_id(db, genre_id)
    if not genre:
        return None

    for key, value in genre_data.model_dump(
            exclude_unset=True
    ).items():
        setattr(genre, key, value)

    await db.commit()
    await db.refresh(genre)
    return genre


async def remove_genre(
        db: AsyncSession,
        genre_id: int
) -> bool:
    """Delete a genre by its ID. Returns True if deleted, else False."""
    result = await db.execute(
        delete(GenreModel)
        .where(GenreModel.id == genre_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_all_stars(
        db: AsyncSession
) -> list[StarModel]:
    """Retrieve all stars from the database, ordered by ID."""
    result = await db.execute(
        select(StarModel)
        .order_by(StarModel.id)
    )
    return list(result.scalars().all())


async def get_star_by_id(
        db: AsyncSession,
        star_id: int
) -> StarModel | None:
    """Retrieve a single star by ID."""
    result = await db.execute(
        select(StarModel)
        .where(StarModel.id == star_id)
    )
    return result.scalar_one_or_none()


async def add_star(
        db: AsyncSession,
        star_data: StarCreateSchema
) -> StarModel:
    """Create a new star with the provided data."""
    try:
        star = StarModel(**star_data.model_dump())
        db.add(star)
        await db.commit()
        await db.refresh(star)
        return star
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Star with this name already exists."
        )


async def edit_star(
        db: AsyncSession,
        star_id: int,
        star_data: StarUpdateSchema
) -> StarModel | None:
    """
    Update an existing star with the provided data.
    Returns the updated star or None if not found.
    """
    star = await get_star_by_id(db, star_id)
    if not star:
        return None

    for key, value in star_data.model_dump(
            exclude_unset=True
    ).items():
        setattr(star, key, value)

    await db.commit()
    await db.refresh(star)
    return star


async def remove_star(
        db: AsyncSession,
        star_id: int
) -> bool:
    """Delete a star by its ID. Returns True if deleted, else False."""
    result = await db.execute(
        delete(StarModel)
        .where(StarModel.id == star_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_all_directors(
        db: AsyncSession
) -> list[DirectorModel]:
    """Retrieve all directors from the database, ordered by ID."""
    result = await db.execute(
        select(DirectorModel)
        .order_by(DirectorModel.id)
    )
    return list(result.scalars().all())


async def get_director_by_id(
        db: AsyncSession,
        director_id: int
) -> DirectorModel | None:
    """Retrieve a single director by ID."""
    result = await db.execute(
        select(DirectorModel)
        .where(DirectorModel.id == director_id)
    )
    return result.scalar_one_or_none()


async def add_director(
        db: AsyncSession,
        director_data: DirectorCreateSchema
) -> DirectorModel:
    """Create a new director with the provided data."""
    try:
        director = DirectorModel(**director_data.model_dump())
        db.add(director)
        await db.commit()
        await db.refresh(director)
        return director
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Director with this name already exists."
        )


async def edit_director(
        db: AsyncSession,
        director_id: int,
        director_data: DirectorCreateSchema
) -> DirectorModel | None:
    """
    Update an existing director with the provided data.
    Returns the updated director or None if not found.
    """
    director = await get_director_by_id(
        db, director_id
    )
    if not director:
        return None

    for key, value in director_data.model_dump(
            exclude_unset=True
    ).items():
        setattr(director, key, value)

    await db.commit()
    await db.refresh(director)
    return director


async def remove_director(
        db: AsyncSession,
        director_id: int
) -> bool:
    """Delete a director by its ID. Returns True if deleted, else False."""
    result = await db.execute(
        delete(DirectorModel)
        .where(DirectorModel.id == director_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_all_certifications(
        db: AsyncSession
) -> list[CertificationModel]:
    """Retrieve all certifications from the database, ordered by ID."""
    result = await db.execute(
        select(CertificationModel)
        .order_by(CertificationModel.id)
    )
    return list(result.scalars().all())


async def get_certification_by_id(
        db: AsyncSession,
        certification_id: int
) -> CertificationModel | None:
    """Retrieve a single certification by ID."""
    result = await db.execute(
        select(CertificationModel)
        .where(CertificationModel.id == certification_id)
    )
    return result.scalar_one_or_none()


async def add_certification(
        db: AsyncSession,
        certification_data: CertificationCreateSchema
) -> CertificationModel:
    """Create a new certification."""
    try:
        certification = CertificationModel(
            **certification_data.model_dump()
        )
        db.add(certification)
        await db.commit()
        await db.refresh(certification)
        return certification
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Certification with this name already exists."
        )


async def edit_certification(
        db: AsyncSession,
        certification_id: int,
        certification_data: CertificationUpdateSchema
) -> CertificationModel | None:
    """
    Update an existing certification.
    Returns the updated certification or None if not found.
    """
    certification = await get_certification_by_id(
        db,
        certification_id
    )
    if not certification:
        return None

    for key, value in certification_data.model_dump(
            exclude_unset=True
    ).items():
        setattr(certification, key, value)

    await db.commit()
    await db.refresh(certification)
    return certification


async def remove_certification(
        db: AsyncSession,
        certification_id: int
) -> bool:
    """Delete a certification by its ID. Returns True if deleted, else False."""
    result = await db.execute(
        delete(CertificationModel)
        .where(CertificationModel.id == certification_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_all_movies(
        db: AsyncSession,
        offset: int, limit: int
) -> list[MovieModel]:
    """Retrieve all movies from the database, ordered by ID."""

    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
            selectinload(MovieModel.certification)
        )
        .offset(offset)
        .limit(limit)
        .order_by(MovieModel.id)
    )
    return list(result.scalars().all())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_movie_by_id(
        db: AsyncSession,
        movie_id: int
) -> MovieModel | None:
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


async def add_movie(
        db: AsyncSession,
        movie_data: MovieCreateSchema
) -> MovieModel:
    """
    Create a new movie including relationships to genres, stars, and directors.
    """

    movie = MovieModel(
        **movie_data.model_dump(
            exclude={"genre_ids", "star_ids", "director_ids"}
        )
    )

    genres_result = await db.execute(
        select(GenreModel)
        .where(GenreModel.id.in_(movie_data.genre_ids))
    )
    genres = genres_result.scalars().all()
    if len(genres) != len(set(movie_data.genre_ids)):
        raise HTTPException(
            status_code=400,
            detail="Some genre IDs not found"
        )
    movie.genres = genres

    stars_result = await db.execute(
        select(StarModel)
        .where(StarModel.id.in_(movie_data.star_ids))
    )
    stars = stars_result.scalars().all()
    if len(stars) != len(set(movie_data.star_ids)):
        raise HTTPException(
            status_code=400,
            detail="Some star IDs not found"
        )
    movie.stars = stars

    directors_result = await db.execute(
        select(DirectorModel)
        .where(DirectorModel.id.in_(movie_data.director_ids))


    )
    directors = directors_result.scalars().all()
    if len(directors) != len(set(movie_data.director_ids)):
        raise HTTPException(
            status_code=400,
            detail="Some director IDs not found"
        )
    movie.directors = directors

    db.add(movie)
    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Movie with this name, year, and time already exists"
        )
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.stars),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.certification),
        )
        .where(MovieModel.id == movie.id)
    )
    movie_with_relations = result.scalar_one()

    return movie_with_relations


async def edit_movie(
        db: AsyncSession,
        movie_id: int,
        data: MovieUpdateSchema
) -> MovieModel | None:
    """
    Update a movie's details and optionally its related genres, stars, and directors.
    Returns the updated movie or None if not found.
    """
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        return None

    for key, value in data.model_dump(
            exclude_unset=True,
            exclude={"genre_ids", "star_ids", "director_ids"}
    ).items():
        setattr(movie, key, value)

    if data.genre_ids:
        movie.genres = await db.execute(

            select(MovieModel.genres.property.mapper.class_)
            .filter(MovieModel.genres
                    .property.mapper.class_.id.in_(data.genre_ids))
        )
    if data.star_ids:
        movie.stars = await db.execute(
            select(MovieModel.stars.property.mapper.class_)
            .filter(MovieModel.stars
                    .property.mapper.class_.id.in_(data.star_ids))
        )
    if data.director_ids:
        movie.directors = await db.execute(
            select(MovieModel.directors.property.mapper.class_)
            .filter(MovieModel.directors
                    .property.mapper.class_.id.in_(data.director_ids))
        )

    await db.commit()
    await db.refresh(movie)
    return movie


async def remove_movie(
        db: AsyncSession,
        movie_id: int
) -> bool:
    """Delete a movie by its ID. Returns True if deleted, else False."""
    result = await db.execute(
        delete(MovieModel)
        .where(MovieModel.id == movie_id)
    )
    await db.commit()
    return result.rowcount > 0
