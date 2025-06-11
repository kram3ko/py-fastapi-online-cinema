from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.dependencies import get_current_user, require_moderator
from crud.movie_service import (
    add_comment,
    add_to_favorites,
    create_certification,
    create_director,
    create_genre,
    create_movie,
    create_star,
    delete_certification,
    delete_director,
    delete_genre,
    delete_movie,
    delete_star,
    get_all_movies_by_genre,
    get_certification,
    get_director,
    get_favorites,
    get_filtered_movies,
    get_genre,
    get_movie_comments,
    get_movie_detail,
    get_star,
    like_or_dislike_movie,
    list_certifications,
    list_directors,
    list_genres,
    list_stars,
    remove_from_favorites,
    search_movies_stmt,
    update_certification,
    update_director,
    update_genre,
    update_movie,
    update_star,
)
from database.deps import get_db
from database.models import MovieModel, OrderItemModel, OrderModel, UserModel
from database.models.orders import OrderStatus
from pagination.pages import Page
from schemas.movies import (
    CertificationCreateSchema,
    CertificationReadSchema,
    CertificationUpdateSchema,
    CommentCreateSchema,
    CommentReadSchema,
    DirectorCreateSchema,
    DirectorReadSchema,
    DirectorUpdateSchema,
    FavoriteCreateSchema,
    FavoriteReadSchema,
    GenreBaseSchema,
    GenreCreateSchema,
    GenreReadSchema,
    GenreUpdateSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieFilterParamsSchema,
    MovieLikeResponseSchema,
    MovieListItemSchema,
    MovieUpdateSchema,
    SortOptions,
    StarCreateSchema,
    StarReadSchema,
    StarUpdateSchema,
)
from security.http import jwt_security

router = APIRouter(dependencies=[Depends(jwt_security)])


@router.get(
    "/genres/",
    response_model=list[GenreReadSchema]
)
async def get_genres(
        db: AsyncSession = Depends(get_db)
) -> list[GenreReadSchema]:

    """
    Get a list of all movie genres with the number of movies of that genre.
    """

    return await list_genres(db)


@router.get(
    "/genres/{genre_id}/",
    response_model=GenreBaseSchema
)
async def get_genre_by_id(
        genre_id: int,
        db: AsyncSession = Depends(get_db)
) -> GenreBaseSchema:

    """
    Retrieve a genre by its ID.
    """

    return await get_genre(db, genre_id)


@router.get(
    "/genres_movies/",
    response_model=list[MovieListItemSchema]
)
async def get_movies_by_genre(
        genre_id: int,
        db: AsyncSession = Depends(get_db)
) -> list[MovieListItemSchema]:

    """
    Enter a genre by its ID and get a list of movies with that genre.
    """

    movies = await get_all_movies_by_genre(db, genre_id)
    return [MovieListItemSchema.model_validate(movie) for movie in movies]


@router.post(
    "/genres/",
    response_model=GenreReadSchema,
    status_code=201,
    dependencies=[Depends(require_moderator)]
)
async def create_movie_genre(
        genre_data: GenreCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> GenreReadSchema:

    """
    Create a new movie genre.
    """

    return GenreReadSchema.model_validate(await create_genre(db, genre_data))


@router.put(
    "/genres/{genre_id}/",
    response_model=GenreReadSchema,
    dependencies=[Depends(require_moderator)]
)
async def update_movie_genre(
        genre_id: int,
        genre_data: GenreUpdateSchema,
        db: AsyncSession = Depends(get_db)

) -> GenreReadSchema:

    """
    Update an existing genre by ID.
    """

    return await update_genre(db, genre_id, genre_data)


@router.delete("/genres/{genre_id}/", dependencies=[Depends(require_moderator)])
async def delete_movie_genre(
        genre_id: int,
        db: AsyncSession = Depends(get_db)
) -> dict[str, str]:

    """
    Delete a genre by its ID.
    """

    success = await delete_genre(db, genre_id)
    if success:
        return {"detail": "Genre deleted successfully"}
    return {"detail": "Genre not found."}


@router.get("/stars/", response_model=list[StarReadSchema])
async def get_stars(
        db: AsyncSession = Depends(get_db)
) -> list[StarReadSchema]:

    """
    Get a list of all movie stars.
    """

    return await list_stars(db)


@router.get("/stars/{star_id}/", response_model=StarReadSchema)
async def get_star_by_id(
        star_id: int,
        db: AsyncSession = Depends(get_db)
) -> StarReadSchema:

    """
    Retrieve a movie star by ID.
    """

    return await get_star(db, star_id)


@router.post("/stars/",
             response_model=StarReadSchema,
             status_code=201,
             dependencies=[Depends(require_moderator)]
             )
async def create_movie_star(
        star_data: StarCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> StarReadSchema:

    """
    Create a new movie star.
    """

    return await create_star(db, star_data)


@router.put("/stars/{star_id}/",
            response_model=StarReadSchema,
            dependencies=[Depends(require_moderator)]
            )
async def update_movie_star(
        star_id: int,
        star_data: StarUpdateSchema,
        db: AsyncSession = Depends(get_db)
) -> StarReadSchema:

    """
    Update a movie star by ID.
    """

    return await update_star(db, star_id, star_data)


@router.delete("/stars/{star_id}/", dependencies=[Depends(require_moderator)])
async def delete_movie_star(
        star_id: int,
        db: AsyncSession = Depends(get_db)
) -> dict[str, str]:

    """
    Delete a movie star by ID.
    """

    success = await delete_star(db, star_id)
    if success:
        return {"detail": "Star deleted successfully"}
    return {"detail": "Star not found."}


@router.get("/directors/",
            response_model=list[DirectorReadSchema]
            )
async def get_directors(
        db: AsyncSession = Depends(get_db)
) -> list[DirectorReadSchema]:

    """
    Get a list of all movie directors.
    """

    return await list_directors(db)


@router.get("/directors/{director_id}/",
            response_model=DirectorReadSchema
            )
async def get_director_by_id(
        director_id: int,
        db: AsyncSession = Depends(get_db)
) -> DirectorReadSchema:

    """
    Retrieve a movie director by ID.
    """

    return await get_director(db, director_id)


@router.post("/directors/",
             response_model=DirectorReadSchema,
             status_code=201,
             dependencies=[Depends(require_moderator)]
             )
async def create_movie_director(
        director_data: DirectorCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> DirectorReadSchema:

    """
    Create a new movie director.
    """

    return await create_director(db, director_data)


@router.put("/director/{director_id}/",
            response_model=DirectorReadSchema,
            dependencies=[Depends(require_moderator)]
            )
async def update_movie_director(
        director_id: int,
        director_data: DirectorUpdateSchema,
        db: AsyncSession = Depends(get_db)
) -> DirectorReadSchema:

    """
    Update a movie director by ID.
    """

    return await update_director(db, director_id, director_data)


@router.delete("/directors/{director_id}/", dependencies=[Depends(require_moderator)])
async def delete_movie_director(
        director_id: int,
        db: AsyncSession = Depends(get_db)
) -> dict[str, str]:

    """
    Delete a movie director by ID.
    """

    return await delete_director(db, director_id)


@router.get("/certifications/",
            response_model=list[CertificationReadSchema]
            )
async def get_certifications(
        db: AsyncSession = Depends(get_db)
) -> list[CertificationReadSchema]:

    """
    Get a list of all movie certifications.
    """

    return await list_certifications(db)


@router.get("/certifications/{certification_id}/",
            response_model=CertificationReadSchema)
async def get_certification_by_id(
        certification_id: int,
        db: AsyncSession = Depends(get_db)
) -> CertificationReadSchema:

    """
    Retrieve a movie certification by ID.
    """

    return await get_certification(db, certification_id)


@router.post("/certifications/",
             response_model=CertificationReadSchema,
             status_code=201,
             dependencies=[Depends(require_moderator)]
             )
async def create_movie_certification(
        certification_data: CertificationCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> CertificationReadSchema:

    """
    Create a new movie certification.
    """

    return await create_certification(db, certification_data)


@router.put("/certification/{certification_id}/",
            response_model=CertificationReadSchema,
            dependencies=[Depends(require_moderator)]
            )
async def update_movie_certification(
        certification_id: int,
        certification_data: CertificationUpdateSchema,
        db: AsyncSession = Depends(get_db)
) -> CertificationReadSchema:

    """
    Update a movie certification by ID.
    """

    return await update_certification(
        db,
        certification_id,
        certification_data
    )


@router.delete("/certifications/{certification_id}/", dependencies=[Depends(require_moderator)])
async def delete_movie_certification(
        certification_id: int,
        db: AsyncSession = Depends(get_db)
) -> dict[str, str]:

    """
    Delete a movie certification by ID.
    """

    return await delete_certification(
        db, certification_id
    )


@router.get("/movies/", response_model=Page[MovieListItemSchema])
async def get_movies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    sort_by: SortOptions | None = Query(None),
    params: Params = Depends(),
    filters: MovieFilterParamsSchema = Depends()
) -> Page[MovieListItemSchema]:

    """
    Get a paginated list of movies filtered by release year,
    rating and sorted by price and rating.
    """

    stmt = await get_filtered_movies(
        db=db,
        filters=filters,
        sort_by=sort_by
    )

    result = await apaginate(
        db,
        stmt,
        params=params,
        additional_data={
            "url": request.url.path.replace("/api/v1", "", 1),
        },
    )

    if not result.items:
        raise HTTPException(status_code=404, detail="No movies found.")

    result.items = [
        MovieListItemSchema(
            id=movie.id,
            name=movie.name,
            year=movie.year,
            imdb=movie.imdb,
            time=movie.time,
            price=movie.price,
            genres=movie.genres
        )
        for movie in result.items
    ]

    return result


@router.get("/movies/search/", response_model=list[MovieDetailSchema])
async def search_movies(
    search: str = Query(..., min_length=2, example="nolan"),
    db: AsyncSession = Depends(get_db),
) -> list[MovieDetailSchema]:

    """
    Search for movies by a keyword in their title, stars, directors or descriptions.
    This endpoint allows users to search for movies using a query string.

    Args:
        search (str): The search keyword with a minimum length of 2 characters.
        db (AsyncSession): The asynchronous database session.
    """

    stmt = await search_movies_stmt(db=db, search=search)
    result = await db.execute(stmt)
    movies = result.scalars().unique().all()
    return movies


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:

    """
    Get detailed information about a movie by its ID.
    """

    return await get_movie_detail(db, movie_id)


@router.post("/movies/",
             response_model=MovieDetailSchema,
             status_code=201,
             dependencies=[Depends(require_moderator)]
             )
async def create_one_movie(
        data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieCreateSchema:

    """
    Create a new movie.
    """

    return await create_movie(db, data)


@router.put("/movies/{movie_id}/",
            response_model=MovieDetailSchema,
            dependencies=[Depends(require_moderator)]
            )
async def update_one_movie(
    movie_id: int, data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:

    """
    Update an existing movie by ID.
    """

    return await update_movie(db, movie_id, data)


@router.delete("/movies/{movie_id}/", dependencies=[Depends(require_moderator)])
async def delete_one_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
) -> dict[str, str]:

    """
    Delete a movie by ID.
    """

    success = await delete_movie(db, movie_id)
    if success:
        return {"detail": "Movie deleted successfully"}
    return {"detail": "Movie not found."}


@router.post("/movies_like/",
             response_model=MovieLikeResponseSchema,
             status_code=200,
             )
async def like_movie(
        movie_id: int,
        is_like: bool = Query(True, description="True = Like, False = Dislike"),
        db: AsyncSession = Depends(get_db),
        user: UserModel = Depends(get_current_user),
) -> MovieLikeResponseSchema:

    """
    Like or dislike a movie.

    This endpoint allows the authenticated user to like or dislike a specific movie.
    If the user has already reacted to the movie, their previous response will be updated.

    Args:
        movie_id (int): The ID of the movie to like or dislike.
        is_like (bool): Query parameter. `True` to like, `False` to dislike.
        db (AsyncSession): The SQLAlchemy asynchronous session, injected by FastAPI.
        user (UserModel): The currently authenticated user, injected by FastAPI.

    Returns:
        MovieLikeResponseSchema: Contains a confirmation message,
        and updated total likes and dislikes.
    """

    return await like_or_dislike_movie(db, movie_id, user, is_like)


@router.post("/movies/comments/", response_model=CommentReadSchema)
async def create_comment(
    movie_id: int,
    data: CommentCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> CommentReadSchema:

    """
    Create a comment for a movie.

    Allows an authenticated user to add a comment to a specific movie.

    Args:
        data (CommentCreateSchema): Data required to create a comment, including movie ID and text.
        db (AsyncSession): Asynchronous SQLAlchemy session.
        current_user (UserModel): Currently authenticated user.

    Returns:
        CommentReadSchema: The created comment and creation time.
    """

    return await add_comment(db, movie_id, current_user.id, data)


@router.get("/movies/{movie_id}/comments/",
            response_model=list[CommentReadSchema],
            )
async def list_comments(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> list[CommentReadSchema]:

    """
    Retrieve all comments for a specific movie.

    Fetches all user comments related to a given movie, ordered by creation time if applicable.

    Args:
        movie_id (int): The ID of the movie to retrieve comments for.
        db (AsyncSession): Asynchronous SQLAlchemy session.

    Returns:
        list[CommentReadSchema]: A list of comments associated with the movie.
    """

    return await get_movie_comments(db, movie_id)


@router.post("/favorites/", response_model=FavoriteReadSchema)
async def add_favorite(
    data: FavoriteCreateSchema,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)
) -> FavoriteReadSchema:

    """
    Add a movie to the user's favorites.

    Adds the specified movie to the authenticated user's list of favorite movies.

    Args:
        data (FavoriteCreateSchema): Schema containing the ID of the movie to add.
        db (AsyncSession): Asynchronous SQLAlchemy session.
        user (UserModel): The currently authenticated user.

    Returns:
        FavoriteReadSchema: The newly added favorite record.
    """

    favorite = await add_to_favorites(db, user.id, data.movie_id)
    return FavoriteReadSchema.from_orm(favorite)


@router.delete("/favorites/{movie_id}/", response_model=str)
async def delete_favorite(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)
) -> str:

    """
    Remove a movie from the user's favorites.

    Deletes the specified movie from the authenticated user's favorites list.

    Args:
        movie_id (int): The ID of the movie to remove.
        db (AsyncSession): Asynchronous SQLAlchemy session.
        user (UserModel): The currently authenticated user.

    """

    return await remove_from_favorites(db, user.id, movie_id)


@router.get("/favorites/", response_model=list[MovieListItemSchema])
async def list_favorites(
    search: str = Query("", description="Search by title"),
    genre_id: int = Query(None),
    sort_by: str = Query("title", enum=["title", "rating"]),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)
) -> list[MovieListItemSchema]:

    """
    Retrieve the user's list of favorite movies.

    Returns all movies marked as favorites by the authenticated user, with optional
    filtering by genre, title search, and sorting.

    Args:
        search (str): Optional search query to filter by movie title.
        genre_id (int | None): Optional genre ID for filtering.
        sort_by (str): Field to sort the results by ("title" or "rating").
        db (AsyncSession): Asynchronous SQLAlchemy session.
        user (UserModel): The currently authenticated user.

    Returns:
        list[MovieListItemSchema]: A list of favorite movies.
    """

    return await get_favorites(db, user.id, search, genre_id, sort_by)
