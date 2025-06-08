from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import add_pagination, paginate
from sqlalchemy.orm import Session

from crud.movie_service import (
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
    get_certification,
    get_director,
    get_genre,
    get_movie_detail,
    get_star,
    list_certifications,
    list_directors,
    list_genres,
    list_movies,
    list_stars,
    update_certification,
    update_director,
    update_genre,
    update_movie,
    update_star,
)
from database.deps import get_db
from database.models import MovieModel
from pagination.pages import Page
from schemas.movies import (
    CertificationCreateSchema,
    CertificationReadSchema,
    CertificationUpdateSchema,
    DirectorCreateSchema,
    DirectorReadSchema,
    DirectorUpdateSchema,
    GenreCreateSchema,
    GenreReadSchema,
    GenreUpdateSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListItemSchema,
    MovieUpdateSchema,
    StarCreateSchema,
    StarReadSchema,
    StarUpdateSchema,
)

router = APIRouter()


@router.get(
    "/genres/",
    response_model=list[GenreReadSchema]
)
async def get_genres(
        db: AsyncSession = Depends(get_db)
) -> list[GenreReadSchema]:

    """
    Get a list of all movie genres.
    """
    return await list_genres(db)


@router.get(
    "/genres/{genre_id}/",
    response_model=GenreReadSchema
)
async def get_genre_by_id(
        genre_id: int,
        db: AsyncSession = Depends(get_db)
) -> GenreReadSchema:

    """
    Retrieve a genre by its ID.
    """
    return await get_genre(db, genre_id)


@router.post(
    "/genres/",
    response_model=GenreReadSchema,
    status_code=201
)
async def create_movie_genre(
        genre_data: GenreCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> GenreReadSchema:

    """
    Create a new genre.
    """
    return GenreReadSchema.model_validate(await create_genre(db, genre_data))


@router.put(
    "/genres/{genre_id}/",
    response_model=GenreReadSchema
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


@router.delete("/genres/{genre_id}/")
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
             status_code=201
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
            response_model=StarReadSchema
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


@router.delete("/stars/{star_id}/")
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
             status_code=201
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
            response_model=DirectorReadSchema
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


@router.delete("/directors/{director_id}/")
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
             status_code=201
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
            response_model=CertificationReadSchema
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


@router.delete("/certifications/{certification_id}/")
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


@router.get("/movies/", response_model=Page)
async def get_movies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    params: Params = Depends(),
) -> Page:
    """
    Get a paginated list of movies.
    """
    result = await apaginate(
        db,
        select(MovieModel).order_by(MovieModel.id.desc()),
        params=params,
        additional_data={
            "url": request.url.path.replace("/api/v1", "", 1),
        },
        additional_data={
            "url": request.url.path.replace("/api/v1", "", 1),
        },
    )

    if not result.results:
        raise HTTPException(status_code=404, detail="No movies found.")

    result.results = [
        MovieListItemSchema.model_validate(movie)
        for movie in result.results
    ]

    return result


@router.get("/movies/", response_model=list[MovieListItemSchema])
def list_movies_with_filters(
    search: str = Query(None),
    release_year: int = Query(None),
    min_rating: float = Query(None),
    max_rating: float = Query(None),
    sort_by: str = Query("release_date"),
    order: str = Query("asc"),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return list_movies_service(
        db=db,
        search=search,
        release_year=release_year,
        min_rating=min_rating,
        max_rating=max_rating,
        sort_by=sort_by,
        order=order,
        skip=skip,
        limit=limit
    )

    if not result.results:
        raise HTTPException(status_code=404, detail="No movies found.")

    result.results = [
        MovieListItemSchema.model_validate(movie)
        for movie in result.results
    ]

    return result


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    """
    Get detailed information about a movie by its ID.
    """
    return await get_movie_detail(movie_id, db)
    return await get_movie_detail(db, movie_id)


@router.post("/movies/",
             response_model=MovieDetailSchema,
             status_code=201
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
            response_model=MovieDetailSchema
            )
async def update_one_movie(
    movie_id: int, data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    movie_id: int,
    data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> MovieUpdateSchema:
    """
    Update an existing movie by ID.
    """
    return await update_movie(db, movie_id, data)


@router.delete("/movies/{movie_id}/")
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
