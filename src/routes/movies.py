from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from database.models.accounts import UserModel
from database.models.movies import MovieModel
from pagination import Page, Params
from pagination.pages import T
from schemas.movies import MovieCreateSchema, MovieDetailSchema, MovieListItemSchema, MovieUpdateSchema

router = APIRouter()


@router.get(
    "/movies/",
    response_model=Page,
    summary="Get a paginated list of movies",
    description=(
        "<h3>This endpoint retrieves a paginated list of movies from the database. "
        "Clients can specify the `page` number and the number of items per page using `per_page`. "
        "The response includes details about the movies, total pages, and total items, "
        "along with links to the previous and next pages if applicable.</h3>"
    ),
    responses={
        404: {
            "description": "No movies found.",
            "content": {"application/json": {"example": {"detail": "No movies found."}}},
        }
    },
)
async def get_movie_list(
    request: Request,
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Fetch a paginated list of movies from the database (asynchronously).

    This function retrieves a paginated list of movies, allowing the client to specify
    the page number and the number of items per page. It calculates the total pages
    and provides links to the previous and next pages when applicable.

    :param request: The FastAPI request object (provided via dependency injection).
    :type request: Request
    :param params: The pagination parameters (provided via dependency injection).
    :type params: Params
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: A response containing the paginated list of movies and metadata.
    :rtype: Page

    :raises HTTPException: Raises a 404 error if no movies are found for the requested page.
    """
    return None


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    summary="Add a new movie",
    description=(
        "<h3>This endpoint allows clients to add a new movie to the database. "
        "It accepts details such as name, date, genres, actors, languages, and "
        "other attributes. The associated country, genres, actors, and languages "
        "will be created or linked automatically.</h3>"
    ),
    responses={
        201: {
            "description": "Movie created successfully.",
        },
        400: {
            "description": "Invalid input.",
            "content": {"application/json": {"example": {"detail": "Invalid input data."}}},
        },
    },
    status_code=201,
)
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema | None:
    """
    Add a new movie to the database.

    This endpoint allows the creation of a new movie with details such as
    name, release date, genres, actors, and languages. It automatically
    handles linking or creating related entities.

    :param movie_data: The data is required to create a new movie.
    :type movie_data: MovieCreateSchema
    :param db: The SQLAlchemy async database session (provided via dependency injection).
    :type db: AsyncSession

    :return: The created movie with all details.
    :rtype: MovieDetailSchema

    :raises HTTPException:
        - 409 if a movie with the same name and date already exists.
        - 400 if input data is invalid (e.g., violating a constraint).
    """
    return None


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    summary="Get movie details by ID",
    description=(
        "<h3>Fetch detailed information about a specific movie by its unique ID. "
        "This endpoint retrieves all available details for the movie, such as "
        "its name, genre, crew, budget, and revenue. If the movie with the given "
        "ID is not found, a 404 error will be returned.</h3>"
    ),
    responses={
        404: {
            "description": "Movie not found.",
            "content": {"application/json": {"example": {"detail": "Movie with the given ID was not found."}}},
        }
    },
)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema | None:
    """
    Retrieve detailed information about a specific movie by its ID.

    This function fetches detailed information about a movie identified by its unique ID.
    If the movie does not exist, a 404 error is returned.

    :param movie_id: The unique identifier of the movie to retrieve.
    :type movie_id: int
    :param db: The SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: The details of the requested movie.
    :rtype: MovieDetailResponseSchema

    :raises HTTPException: Raises a 404 error if the movie with the given ID is not found.
    """
    return None


@router.delete(
    "/movies/{movie_id}/",
    summary="Delete a movie by ID",
    description=(
        "<h3>Delete a specific movie from the database by its unique ID.</h3>"
        "<p>If the movie exists, it will be deleted. If it does not exist, "
        "a 404 error will be returned.</p>"
    ),
    responses={
        204: {"description": "Movie deleted successfully."},
        404: {
            "description": "Movie not found.",
            "content": {"application/json": {"example": {"detail": "Movie with the given ID was not found."}}},
        },
    },
    status_code=204,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a specific movie by its ID.

    This function deletes a movie identified by its unique ID.
    If the movie does not exist, a 404 error is raised.

    :param movie_id: The unique identifier of the movie to delete.
    :type movie_id: int
    :param db: The SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :raises HTTPException: Raises a 404 error if the movie with the given ID is not found.

    :return: A response indicating the successful deletion of the movie.
    :rtype: None
    """
    pass


@router.patch(
    "/movies/{movie_id}/",
    summary="Update a movie by ID",
    description=(
        "<h3>Update details of a specific movie by its unique ID.</h3>"
        "<p>This endpoint updates the details of an existing movie. If the movie with "
        "the given ID does not exist, a 404 error is returned.</p>"
    ),
    responses={
        200: {
            "description": "Movie updated successfully.",
            "content": {"application/json": {"example": {"detail": "Movie updated successfully."}}},
        },
        404: {
            "description": "Movie not found.",
            "content": {"application/json": {"example": {"detail": "Movie with the given ID was not found."}}},
        },
    },
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Update a specific movie by its ID.

    This function updates a movie identified by its unique ID.
    If the movie does not exist, a 404 error is raised.

    :param movie_id: The unique identifier of the movie to update.
    :type movie_id: int
    :param movie_data: The updated data for the movie.
    :type movie_data: MovieUpdateSchema
    :param db: The SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :raises HTTPException: Raises a 404 error if the movie with the given ID is not found.

    :return: A response indicating the successful update of the movie.
    :rtype: None
    """
    pass
