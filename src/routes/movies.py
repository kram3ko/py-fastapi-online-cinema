from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from crud.movie_service import (
    list_genres,
    get_genre,
    create_genre,
    update_genre,
    delete_genre,
    list_stars,
    get_star,
    create_star,
    update_star,
    delete_star,
    list_movies
)
from database import get_db
from pagination import Page
from schemas.movies import (
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieDetailSchema,
    MovieListItemSchema,
    GenreReadSchema,
    GenreCreateSchema,
    GenreUpdateSchema,
    StarReadSchema,
    StarCreateSchema,
    StarUpdateSchema
)


router = APIRouter()


@router.get(
    "/genres/",
    response_model=list[GenreReadSchema]
)
async def get_genres(db: AsyncSession = Depends(get_db)) -> list[GenreReadSchema]:
    """
    Get a list of all movie genres.
    """
    return await list_genres(db)


@router.get(
    "/genres/{genre_id}/",
    response_model=GenreReadSchema
)
async def get_genre_by_id(genre_id: int, db: AsyncSession = Depends(get_db)) -> GenreReadSchema:
    """
    Retrieve a genre by its ID.
    """
    return await get_genre(db, genre_id)


@router.post(
    "/genres/",
    response_model=GenreReadSchema,
    status_code=201
)
async def create_genre(genre_data: GenreCreateSchema, db: AsyncSession = Depends(get_db)) -> GenreReadSchema:
    """
    Create a new genre.
    """
    return await create_genre(db, genre_data)


@router.put(
    "/genres/{genre_id}/",
    response_model=GenreReadSchema
)
async def update_genre(genre_id: int, genre_data: GenreUpdateSchema, db: AsyncSession = Depends(get_db)) -> GenreReadSchema:
    """
    Update an existing genre by ID.
    """
    return await update_genre(db, genre_id, genre_data)


@router.delete("/genres/{genre_id}/")
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Delete a genre by its ID.
    """
    return await delete_genre(db, genre_id)


@router.get("/stars/", response_model=list[StarReadSchema])
async def get_stars(db: AsyncSession = Depends(get_db)) -> list[StarReadSchema]:
    """
    Get a list of all movie stars.
    """
    return await list_stars(db)


@router.get("/stars/{star_id}/", response_model=StarReadSchema)
async def get_star_by_id(star_id: int, db: AsyncSession = Depends(get_db)) -> StarReadSchema:
    """
    Retrieve a movie star by ID.
    """
    return await get_star(db, star_id)


@router.post("/stars/", response_model=StarReadSchema, status_code=201)
async def create_star(star_data: StarCreateSchema, db: AsyncSession = Depends(get_db)) -> StarReadSchema:
    """
    Create a new movie star.
    """
    return await create_star(db, star_data)


@router.put("/stars/{star_id}/", response_model=StarReadSchema)
async def update_star(star_id: int, star_data: StarUpdateSchema, db: AsyncSession = Depends(get_db)) -> StarReadSchema:
    """
    Update a movie star by ID.
    """
    return await update_star(db, star_id, star_data)


@router.delete("/stars/{star_id}/")
async def delete_star(star_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Delete a movie star by ID.
    """
    return await delete_star(db, star_id)


@router.get(
    "/movies/",
    response_model=Page[MovieListItemSchema]
)
async def get_movies(
        db: AsyncSession = Depends(get_db),
) -> Page[MovieListItemSchema]:
    """
    Get a paginated list of movies.
    """
    return await list_movies(db)


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema
)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    """
    Get detailed information about a movie by its ID.
    """
    return await get_movies(db, movie_id)


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(data: MovieCreateSchema, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:
    """
    Create a new movie.
    """
    return await create_movie(db, data)


@router.put("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def update_movie(movie_id: int, data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:
    """
    Update an existing movie by ID.
    """
    return await update_movie(db, movie_id, data)


@router.delete("/movies/{movie_id}/")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Delete a movie by ID.
    """
    return await delete_movie(db, movie_id)
