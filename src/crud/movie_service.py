from fastapi import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate as apaginate
from sqlalchemy.ext.asyncio import AsyncSession

from crud import movie_crud
from database.models.movies import GenreModel, MovieModel, StarModel
from schemas.movies import (
    GenreCreateSchema,
    GenreUpdateSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListItemSchema,
    MovieUpdateSchema,
    StarCreateSchema,
    StarUpdateSchema,
)


async def list_genres(db: AsyncSession) -> list[GenreModel]:
    """
    Retrieve all movie genres from the database.
    :param db: Async database session.
    :return: List of GenreModel instances.
    """
    return await movie_crud.get_all_genres(db)


async def get_genre(db: AsyncSession, genre_id: int) -> GenreModel:
    """
    Get a specific genre by its ID.
    :param db: Async database session.
    :param genre_id: ID of the genre to retrieve.
    :raises HTTPException: If genre is not found.
    :return: GenreModel instance.
    """
    genre = await movie_crud.get_genre_by_id(db, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")
    return genre


async def create_genre(db: AsyncSession, genre_data: GenreCreateSchema) -> GenreModel:
    """
    Create a new genre in the database.
    :param db: Async database session.
    :param genre_data: Genre creation schema.
    :return: Created GenreModel instance.
    """
    return await movie_crud.create_genre(db, genre_data)


async def update_genre(db: AsyncSession, genre_id: int, genre_data: GenreUpdateSchema) -> GenreModel:
    """
    Update an existing genre by ID.
    :param db: Async database session.
    :param genre_id: ID of the genre to update.
    :param genre_data: Data to update.
    :raises HTTPException: If genre is not found.
    :return: Updated GenreModel instance.
    """
    updated = await movie_crud.update_genre(db, genre_id, genre_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Genre not found.")
    return updated


async def delete_genre(db: AsyncSession, genre_id: int) -> dict[str, str]:
    """
    Delete a genre by ID.
    :param db: Async database session.
    :param genre_id: ID of the genre to delete.
    :raises HTTPException: If genre is not found.
    :return: Success message dict.
    """
    deleted = await movie_crud.delete_genre(db, genre_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Genre not found.")
    return {"detail": "Genre deleted successfully."}


async def list_stars(db: AsyncSession) -> list[StarModel]:
    """
    Retrieve all movie stars from the database.
    :param db: Async database session.
    :return: List of StarModel instances.
    """
    return await movie_crud.get_all_stars(db)


async def get_star(db: AsyncSession, star_id: int) -> StarModel:
    """
    Get a specific star by ID.
    :param db: Async database session.
    :param star_id: ID of the star to retrieve.
    :raises HTTPException: If star is not found.
    :return: StarModel instance.
    """
    star = await movie_crud.get_star_by_id(db, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found.")
    return star


async def create_star(db: AsyncSession, star_data: StarCreateSchema) -> StarModel:
    """
    Create a new movie star.
    :param db: Async database session.
    :param star_data: Star creation schema.
    :return: Created StarModel instance.
    """
    return await movie_crud.create_star(db, star_data)


async def update_star(db: AsyncSession, star_id: int, star_data: StarUpdateSchema) -> StarModel:
    """
    Update a movie star by ID.
    :param db: Async database session.
    :param star_id: ID of the star to update.
    :param star_data: Data to update.
    :raises HTTPException: If star is not found.
    :return: Updated StarModel instance.
    """
    updated = await movie_crud.update_star(db, star_id, star_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Star not found.")
    return updated


async def delete_star(db: AsyncSession, star_id: int) -> dict[str, str]:
    """
    Delete a movie star by ID.
    :param db: Async database session.
    :param star_id: ID of the star to delete.
    :raises HTTPException: If star is not found.
    :return: Success message dict.
    """
    deleted = await movie_crud.delete_star(db, star_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Star not found.")
    return {"detail": "Star deleted successfully."}


async def list_movies(db: AsyncSession) -> list[MovieModel]:
    """
    Retrieve all movies from the database.
    :param db: Async database session.
    :return: List of MovieModel instances.
    """
    return await movie_crud.get_all_movies(db)


async def get_paginated_movies(db: AsyncSession, params: Params) -> Page[MovieListItemSchema]:
    """
    Retrieve paginated list of movies using FastAPI pagination.
    :param db: Async database session.
    :param params: Pagination parameters.
    :raises HTTPException: If no movies found.
    :return: Paginated result with validated MovieListItemSchema items.
    """
    result = await apaginate(db, movie_crud.get_all_movies_stmt(), params=params)

    if not result.results:
        raise HTTPException(status_code=404, detail="No movies found.")

    result.results = [MovieListItemSchema.model_validate(movie) for movie in result.results]

    return result


async def get_movie(db: AsyncSession, movie_id: int) -> MovieModel:
    """
    Get movie by ID.
    :param db: Async database session.
    :param movie_id: ID of the movie.
    :raises HTTPException: If movie is not found.
    :return: MovieModel instance.
    """
    movie = await movie_crud.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")
    return movie


async def get_movie_detail(movie_id: int, db: AsyncSession) -> MovieDetailSchema:
    """
    Get detailed movie info by ID with related data.
    :param movie_id: ID of the movie.
    :param db: Async database session.
    :raises HTTPException: If movie is not found.
    :return: MovieDetailSchema instance.
    """
    movie = await movie_crud.get_movie_by_id(movie_id, db)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    return MovieDetailSchema.model_validate(movie)


async def create_movie(db: AsyncSession, data: MovieCreateSchema) -> MovieModel:
    """
    Create a new movie.
    :param db: Async database session.
    :param data: Movie creation schema.
    :return: Created MovieModel instance.
    """
    return await movie_crud.create_movie(db, data)


async def update_movie(db: AsyncSession, movie_id: int, data: MovieUpdateSchema) -> MovieModel:
    """
    Update movie data by ID.
    :param db: Async database session.
    :param movie_id: ID of the movie to update.
    :param data: Update schema with optional fields.
    :raises HTTPException: If movie is not found.
    :return: Updated MovieModel instance.
    """
    movie = await movie_crud.update_movie(db, movie_id, data)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")
    return movie


async def delete_movie(db: AsyncSession, movie_id: int) -> dict[str, str]:
    """
    Delete a movie by ID.
    :param db: Async database session.
    :param movie_id: ID of the movie to delete.
    :raises HTTPException: If movie is not found.
    :return: Success message dict.
    """
    deleted = await movie_crud.delete_movie(db, movie_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Movie not found.")
    return {"detail": "Movie deleted successfully."}
