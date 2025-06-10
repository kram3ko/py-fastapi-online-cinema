from fastapi import HTTPException
from sqlalchemy import Select, and_, delete, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud import movie_crud
from database.models import OrderItemModel, UserModel
from database.models.movies import (
    CertificationModel,
    CommentModel,
    DirectorModel,
    GenreModel,
    MovieLikeModel,
    MovieModel,
    StarModel,
)
from schemas.movies import (
    CertificationCreateSchema,
    CertificationUpdateSchema,
    CommentCreateSchema,
    DirectorCreateSchema,
    DirectorUpdateSchema,
    GenreCreateSchema,
    GenreUpdateSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieFilterParamsSchema,
    MovieLikeResponseSchema,
    MovieUpdateSchema,
    SortOptions,
    StarCreateSchema,
    StarUpdateSchema,
)


async def list_genres(
        db: AsyncSession
) -> list[GenreModel]:

    """
    Retrieve all movie genres from the database.
    :param db: Async database session.
    :return: List of GenreModel instances.
    """

    return await movie_crud.get_all_genres(db)


async def get_all_movies_by_genre(
        db: AsyncSession,
        genre_id: int
) -> list[MovieModel]:

    """
    Get a specific genre by its ID.
    :param db: Async database session.
    :param genre_id: ID of the genre to retrieve.
    :raises HTTPException: If genre is not found.
    :return: GenreModel instance.
    """

    genre = await movie_crud.get_movie_by_genre(db, genre_id)
    if not genre:
        raise HTTPException(
            status_code=404,
            detail="Genre not found."
        )
    return genre


async def get_genre(
        db: AsyncSession,
        genre_id: int
) -> GenreModel:

    """
    Get a specific genre by ID.
    :param db: Async database session.
    :param genre_id: ID of the genre to retrieve.
    :raises HTTPException: If gener is not found.
    :return: GenerModel instance.
    """

    genre = await movie_crud.get_genre_by_id(db, genre_id)
    if not genre:
        raise HTTPException(
            status_code=404,
            detail="Genre not found."
        )
    return genre


async def create_genre(
        db: AsyncSession,
        genre_data: GenreCreateSchema
) -> GenreModel:

    """
    Create a new genre in the database.
    :param db: Async database session.
    :param genre_data: Genre creation schema.
    :return: Created GenreModel instance.
    """

    return await movie_crud.add_genre(db, genre_data)


async def update_genre(
        db: AsyncSession,
        genre_id: int,
        genre_data: GenreUpdateSchema
) -> GenreModel:

    """
    Update an existing genre by ID.
    :param db: Async database session.
    :param genre_id: ID of the genre to update.
    :param genre_data: Data to update.
    :raises HTTPException: If genre is not found.
    :return: Updated GenreModel instance.
    """

    updated = await movie_crud.edit_genre(
        db,
        genre_id,
        genre_data
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Genre not found."
        )
    return updated


async def delete_genre(
        db: AsyncSession,
        genre_id: int
) -> dict[str, str]:

    """
    Delete a genre by ID.
    :param db: Async database session.
    :param genre_id: ID of the genre to delete.
    :raises HTTPException: If genre is not found.
    :return: Success message dict.
    """

    deleted = await movie_crud.remove_genre(db, genre_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Genre not found."
        )
    return {"detail": "Genre deleted successfully."}


async def list_stars(
        db: AsyncSession
) -> list[StarModel]:

    """
    Retrieve all movie stars from the database.
    :param db: Async database session.
    :return: List of StarModel instances.
    """

    return await movie_crud.get_all_stars(db)


async def get_star(
        db: AsyncSession,
        star_id: int
) -> StarModel:

    """
    Get a specific star by ID.
    :param db: Async database session.
    :param star_id: ID of the star to retrieve.
    :raises HTTPException: If star is not found.
    :return: StarModel instance.
    """

    star = await movie_crud.get_star_by_id(db, star_id)
    if not star:
        raise HTTPException(
            status_code=404,
            detail="Star not found."
        )
    return star


async def create_star(
        db: AsyncSession,
        star_data: StarCreateSchema
) -> StarModel:

    """
    Create a new movie star.
    :param db: Async database session.
    :param star_data: Star creation schema.
    :return: Created StarModel instance.
    """

    return await movie_crud.add_star(db, star_data)


async def update_star(
        db: AsyncSession,
        star_id: int,
        star_data: StarUpdateSchema
) -> StarModel:

    """
    Update a movie star by ID.
    :param db: Async database session.
    :param star_id: ID of the star to update.
    :param star_data: Data to update.
    :raises HTTPException: If star is not found.
    :return: Updated StarModel instance.
    """

    updated = await movie_crud.edit_star(db, star_id, star_data)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Star not found."
        )
    return updated


async def delete_star(
        db: AsyncSession,
        star_id: int
) -> dict[str, str]:

    """
    Delete a movie star by ID.
    :param db: Async database session.
    :param star_id: ID of the star to delete.
    :raises HTTPException: If star is not found.
    :return: Success message dict.
    """

    deleted = await movie_crud.remove_star(db, star_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Star not found."
        )
    return {"detail": "Star deleted successfully."}


async def list_directors(
        db: AsyncSession
) -> list[DirectorModel]:

    """
    Retrieve all directors from the database.
    :param db: Async database session.
    :return: List of director instances.
    """

    return await movie_crud.get_all_directors(db)


async def get_director(
        db: AsyncSession,
        director_id: int
) -> DirectorModel:

    """
    Retrieve a specific director by ID.
    :param db: Async database session.
    :param director_id: ID of the director to retrieve.
    :raises HTTPException: If director is not found.
    :return: Director instance.
    """

    director = await movie_crud.get_director_by_id(
        db,
        director_id
    )
    if not director:
        raise HTTPException(
            status_code=404,
            detail="Director not found."
        )
    return director


async def create_director(
        db: AsyncSession,
        director_data: DirectorCreateSchema
) -> DirectorModel:

    """
    Create a new director.
    :param db: Async database session.
    :param director_data: Data for the new director.
    :return: Created director instance.
    """

    return await movie_crud.add_director(db, director_data)


async def update_director(
        db: AsyncSession,
        director_id: int,
        director_data: DirectorUpdateSchema
) -> DirectorModel:

    """
    Update an existing director by ID.
    :param db: Async database session.
    :param director_id: ID of the director to update.
    :param director_data: New data for the director.
    :raises HTTPException: If director is not found.
    :return: Updated director instance.
    """

    updated = await movie_crud.edit_director(
        db,
        director_id,
        director_data
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Director not found."
        )
    return updated


async def delete_director(
        db: AsyncSession,
        director_id: int
) -> dict[str, str]:

    """
    Delete a director by ID.
    :param db: Async database session.
    :param director_id: ID of the director to delete.
    :raises HTTPException: If director is not found.
    :return: Success message dict.
    """

    deleted = await movie_crud.remove_director(db, director_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Director not found."
        )
    return {"detail": "Director deleted successfully."}


async def list_certifications(
        db: AsyncSession
) -> list[CertificationModel]:

    """
    Retrieve all certifications from the database.
    :param db: Async database session.
    :return: List of certification instances.
    """

    return await movie_crud.get_all_certifications(db)


async def get_certification(
        db: AsyncSession,
        certification_id: int
) -> CertificationModel:

    """
    Retrieve a specific certification by ID.
    :param db: Async database session.
    :param certification_id: ID of the certification to retrieve.
    :raises HTTPException: If certification is not found.
    :return: Certification instance.
    """

    certification = await movie_crud.get_certification_by_id(
        db, certification_id
    )
    if not certification:
        raise HTTPException(
            status_code=404,
            detail="Certification not found."
        )
    return certification


async def create_certification(
        db: AsyncSession,
        certification_data: CertificationCreateSchema
) -> CertificationModel:

    """
    Create a new certification.
    :param db: Async database session.
    :param certification_data: Data for the new certification.
    :return: Created certification instance.
    """

    return await movie_crud.add_certification(
        db,
        certification_data
    )


async def update_certification(
        db: AsyncSession,
        certification_id: int,
        certification_data: CertificationUpdateSchema
) -> CertificationModel:

    """
    Update an existing certification by ID.
    :param db: Async database session.
    :param certification_id: ID of the certification to update.
    :param certification_data: New data for the certification.
    :raises HTTPException: If certification is not found.
    :return: Updated certification instance.
    """

    updated = await movie_crud.edit_certification(
        db, certification_id,
        certification_data
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Certification not found."
        )
    return updated


async def delete_certification(
        db: AsyncSession,
        certification_id: int
) -> dict[str, str]:

    """
    Delete a certification by ID.
    :param db: Async database session.
    :param certification_id: ID of the certification to delete.
    :raises HTTPException: If certification is not found.
    :return: Success message dict.
    """

    deleted = await movie_crud.remove_certification(
        db,
        certification_id
    )
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Certification not found."
        )
    return {"detail": "Certification deleted successfully."}


async def count_movies(db: AsyncSession) -> int:

    """
    Returns the total number of movies in the database.
    Args:
        db (AsyncSession): An asynchronous SQLAlchemy session for database access.
    Returns:
        int: The number of movie records in the MovieModel table. Returns 0 if there are no records.
    """

    stmt = select(func.count(MovieModel.id))
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_filtered_movies(
        db: AsyncSession,
        filters: MovieFilterParamsSchema,
        sort_by: SortOptions | None = None,
) -> Select:

    """
    Builds a SQLAlchemy statement to retrieve movies from the database
    based on provided filter and sorting parameters.

    Args:
        db (AsyncSession): An asynchronous SQLAlchemy session for database access.
        filters (MovieFilterParamsSchema):
        Object containing filtering criteria such as year, IMDb rating, and genre IDs.
        sort_by (SortOptions | None): Optional sorting option to order the results (e.g. by year or rating).

    Returns:
        Select: A SQLAlchemy Select statement with applied filters and sorting.
    """

    stmt = select(MovieModel).options(selectinload(MovieModel.genres))
    conditions = []

    if filters.year:
        conditions.append(MovieModel.year == filters.year)

    if filters.min_imdb:
        conditions.append(MovieModel.imdb >= filters.min_imdb)

    if filters.genre_ids:
        conditions.append(MovieModel.genres.any(GenreModel.id.in_(filters.genre_ids)))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = apply_sorting(stmt, sort_by)
    return stmt


def apply_sorting(stmt, sort_by: SortOptions | None) -> Select:

    """
    Applies sorting to a SQLAlchemy statement based on the given sort option.
    Args:
        stmt: A SQLAlchemy Select statement to which sorting will be applied.
        sort_by (SortOptions | None): An optional enum value indicating the sorting criteria.
            Supported options include:
                - price_asc: Sort by movie price in ascending order.
                - price_desc: Sort by movie price in descending order.
                - release_date_asc: Sort by release year in ascending order.
                - release_date_desc: Sort by release year in descending order.
                - (default): Sort by movie name in descending order.

    Returns:
        The SQLAlchemy Select statement with the appropriate ORDER BY clause applied.
    """

    if sort_by == SortOptions.price_asc:
        stmt = stmt.order_by(MovieModel.price.asc())
    elif sort_by == SortOptions.price_desc:
        stmt = stmt.order_by(MovieModel.price.desc())
    elif sort_by == SortOptions.release_date_asc:
        stmt = stmt.order_by(MovieModel.year.asc())
    elif sort_by == SortOptions.release_date_desc:
        stmt = stmt.order_by(MovieModel.year.desc())
    # elif sort_by == SortOptions.popularity_desc:
    #     stmt = stmt.order_by(MovieModel.likes.desc())
    else:
        stmt = stmt.order_by(MovieModel.name.desc())
    return stmt


async def search_movies_stmt(db: AsyncSession, search: str) -> Select:

    """
    Builds a SQLAlchemy statement to search for movies by name, description,
    star name, or director name using a case-insensitive partial match.

    Args:
        db: An asynchronous SQLAlchemy session (not used directly in the function,
            but likely passed for consistency with other async DB functions).
        search (str): The search string to match against movie names, descriptions,
            star names, and director names.

    Returns:
        Select: A SQLAlchemy Select statement that performs the search with outer joins
        and eager loading of related models (stars, directors, genres).
    """

    search_term = f"%{search.lower()}%"
    stmt = (
        select(MovieModel)
        .distinct()
        .options(
            selectinload(MovieModel.stars),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.genres),
        )
        .outerjoin(MovieModel.stars)
        .outerjoin(MovieModel.directors)
        .where(
            or_(
                func.lower(MovieModel.name).ilike(search_term),
                func.lower(MovieModel.descriptions).ilike(search_term),
                func.lower(StarModel.name).ilike(search_term),
                func.lower(DirectorModel.name).ilike(search_term),
            )
        )
        .order_by(MovieModel.id.desc())
    )

    return stmt


async def get_movie_detail(
        movie_id: int, db: AsyncSession
) -> MovieModel:

    """
    Get detailed movie info by ID with related data.
    :param movie_id: ID of the movie.
    :param db: Async database session.
    :raises HTTPException: If movie is not found.
    :return: MovieDetailSchema instance.
    """

    movie = await movie_crud.get_movie_by_id(movie_id, db)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie not found."
        )

    return MovieDetailSchema.model_validate(movie)


async def create_movie(
        db: AsyncSession,
        data: MovieCreateSchema
) -> MovieModel:

    """
    Create a new movie.
    :param db: Async database session.
    :param data: Movie creation schema.
    :return: Created MovieModel instance.
    """

    return await movie_crud.add_movie(db, data)


async def update_movie(
        db: AsyncSession,
        movie_id: int, data: MovieUpdateSchema
) -> MovieModel:

    """
    Update movie data by ID.
    :param db: Async database session.
    :param movie_id: ID of the movie to update.
    :param data: Update schema with optional fields.
    :raises HTTPException: If movie is not found.
    :return: Updated MovieModel instance.
    """

    movie = await movie_crud.edit_movie(db, movie_id, data)
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie not found."
        )
    return movie


async def delete_movie(
        db: AsyncSession,
        movie_id: int
) -> dict[str, str]:

    """
    Delete a movie by ID.
    :param db: Async database session.
    :param movie_id: ID of the movie to delete.
    :raises HTTPException: If movie is not found.
    :return: Success message dict.
    """

    query = select(exists().where(OrderItemModel.movie_id == movie_id))
    result = await db.execute(query)
    is_ordered = result.scalar()

    if is_ordered:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a movie that has been ordered by at least one user."
        )

    deleted = await movie_crud.remove_movie(db, movie_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Movie not found."
        )
    return {"detail": "Movie deleted successfully."}


async def like_or_dislike_movie(
        db: AsyncSession,
        movie_id: int,
        user: UserModel,
        is_like: bool
) -> MovieLikeResponseSchema:

    """
    Like or dislike a movie on behalf of the authenticated user.

    This function allows a user to express a like (`True`) or dislike (`False`)
    for a movie. If the user has already reacted to the movie, their response is updated.
    Otherwise, a new like/dislike entry is created.

    The function also returns the updated total number of likes and dislikes for the movie.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous database session.
        movie_id (int): The ID of the movie to like or dislike.
        user (UserModel): The currently authenticated user performing the action.
        data (Query): Query parameter indicating the user's response. True = like, False = dislike.

    Returns:
        MovieLikeResponseSchema: A response schema containing a confirmation message,
        and the total number of likes and dislikes for the movie.

    Raises:
        HTTPException: If the movie with the given ID does not exist.
    """

    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt = select(MovieLikeModel).where(
        MovieLikeModel.movie_id == movie_id,
        MovieLikeModel.user_id == user.id
    )
    result = await db.execute(stmt)
    like_obj = result.scalar_one_or_none()

    if like_obj:
        like_obj.is_like = is_like
        message = "The response has been updated. Thanks for the response!"
    else:
        like_obj = MovieLikeModel(
            user_id=user.id,
            movie_id=movie_id,
            is_like=is_like
        )
        db.add(like_obj)
        message = "Thanks for the response!"

    await db.commit()

    total_stmt = select(
        func.count().filter(MovieLikeModel.is_like == True), # noqa E712
        func.count().filter(MovieLikeModel.is_like == False) # noqa E712
    ).where(MovieLikeModel.movie_id == movie_id)

    total_result = await db.execute(total_stmt)
    total_likes, total_dislikes = total_result.one()

    return MovieLikeResponseSchema(
        message=message,
        total_likes=total_likes,
        total_dislikes=total_dislikes
    )


async def add_comment(
        db: AsyncSession,
        movie_id: int,
        user_id: int,
        data: CommentCreateSchema
) -> CommentModel:

    """
    Add a new comment to a movie.

    Creates and stores a comment in the database associated with a specific movie and user.

    Args:
        db (AsyncSession): Asynchronous SQLAlchemy session.
        user_id (int): ID of the user making the comment.
        data (CommentCreateSchema): Data containing the movie ID and comment content.

    Returns:
        CommentModel: The created comment instance.
    """

    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    comment = CommentModel(
        content=data.content,
        rating=data.rating,
        movie_id=movie_id,
        user_id=user_id
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    result = await db.execute(
        select(func.avg(CommentModel.rating)).where(CommentModel.movie_id == movie_id)
    )
    average_rating = result.scalar()

    await db.execute(
        update(MovieModel)
        .where(MovieModel.id == movie_id)
        .values(meta_score=average_rating)
    )

    await db.commit()

    return comment


async def get_movie_comments(
        db: AsyncSession,
        movie_id: int
) -> list[CommentModel]:

    """
    Retrieve comments for a given movie.

    Fetches all comments from the database that are associated with the specified movie,
    ordered by creation time in descending order (most recent first).

    Args:
        db (AsyncSession): Asynchronous SQLAlchemy session.
        movie_id (int): ID of the movie to retrieve comments for.

    Returns:
        list[CommentModel]: A list of comments related to the movie.
    """

    result = await db.execute(
        select(CommentModel)
        .filter_by(movie_id=movie_id)
        .order_by(CommentModel.created_at.desc())
    )
    return list(result.scalars().all())


# async def add_favorite(db: AsyncSession, user_id: int, movie_id: int) -> None:
#     favorite = FavoriteMovieModel(user_id=user_id, movie_id=movie_id)
#     db.add(favorite)
#     try:
#         await db.commit()
#     except IntegrityError:
#         await db.rollback()
#         raise HTTPException(status_code=400, detail="Movie already in favorites.")
#
#
# async def remove_favorite(db: AsyncSession, user_id: int, movie_id: int) -> None:
#     result = await db.execute(
#         delete(FavoriteMovieModel).where(
#             FavoriteMovieModel.user_id == user_id,
#             FavoriteMovieModel.movie_id == movie_id
#         )
#     )
#     if result.rowcount == 0:
#         raise HTTPException(status_code=404, detail="Favorite not found.")
#     await db.commit()
#
#
# async def get_user_favorites(
#     db: AsyncSession,
#     user_id: int,
#     name: str | None = None,
#     genres: str | None = None,
#     sort_by: str = "name",
#     desc: bool = False
# ) -> list[MovieModel]:
#
#     stmt = (
#         select(MovieModel)
#         .join(FavoriteMovieModel, FavoriteMovieModel.movie_id == MovieModel.id)
#         .where(FavoriteMovieModel.user_id == user_id)
#     )
#
#     if name:
#         stmt = stmt.where(MovieModel.name.ilike(f"%{name}%"))
#
#     if genres:
#         stmt = stmt.join(MovieModel.genres).where(GenreModel.name == genres)
#
#     sort_column = getattr(MovieModel, sort_by, MovieModel.name)
#     stmt = stmt.order_by(sort_column.desc() if desc else sort_column)
#
#     result = await db.execute(stmt)
#     return result.scalars().all()
