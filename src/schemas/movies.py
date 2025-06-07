from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from schemas.examples.movies import (
    certification_schema_example,
    director_schema_example,
    genre_schema_example,
    movie_create_schema_example,
    movie_detail_schema_example,
    movie_item_schema_example,
    movie_list_response_schema_example,
    movie_update_schema_example,
    star_schema_example, movie_list_schema_example,
)
import uuid



class GenreBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                genre_schema_example
            ]
        }
    )


class GenreCreateSchema(GenreBaseSchema):
    pass


class GenreUpdateSchema(GenreBaseSchema):
    pass


class GenreDeleteSchema(GenreBaseSchema):
    pass


class GenreReadSchema(GenreBaseSchema):
    id: int
    movie_count: Optional[int] = Field(None, example=12)

    model_config = ConfigDict(from_attributes=True)


class StarBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                star_schema_example
            ]
        }
    )


class StarCreateSchema(StarBaseSchema):
    pass


class StarUpdateSchema(StarBaseSchema):
    pass


class StarDeleteSchema(StarBaseSchema):
    pass


class StarReadSchema(StarBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DirectorBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                director_schema_example
            ]
        }
    )


class DirectorCreateSchema(DirectorBaseSchema):
    pass


class DirectorUpdateSchema(DirectorBaseSchema):
    pass


class DirectorDeleteSchema(DirectorBaseSchema):
    pass


class DirectorReadSchema(DirectorBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CertificationBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                certification_schema_example
            ]
        }
    )


class CertificationCreateSchema(CertificationBaseSchema):
    pass


class CertificationUpdateSchema(CertificationBaseSchema):
    pass


class CertificationDeleteSchema(CertificationBaseSchema):
    pass


class CertificationReadSchema(CertificationBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieBaseSchema(BaseModel):
    uuid_movie: uuid.UUID
    name: str
    year: int
    time: int
    imdb: Optional[float]
    votes: Optional[int]
    meta_score: Optional[float]
    gross: Optional[float]
    descriptions: str
    price: float
    certification_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                movie_item_schema_example
            ]
        }
    )


class MovieDetailSchema(MovieBaseSchema):
    id: int
    genres: list[GenreBaseSchema]
    stars: list[StarBaseSchema]
    directors: list[DirectorBaseSchema]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": movie_detail_schema_example
        }
    )


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    time: int
    genres: list[GenreBaseSchema]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": movie_list_schema_example
        }
    )


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                movie_list_response_schema_example
            ]
        }
    )


class MovieCreateSchema(BaseModel):
    name: str
    year: int
    time: int
    gross: Optional[float]
    descriptions: str
    price: float
    certification_id: int
    genre_ids: list[int]
    star_ids: list[int]
    director_ids: list[int]


    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                movie_create_schema_example
            ]
        }
    )


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    descriptions: Optional[str] = None
    price: Optional[float] = None
    certification_id: Optional[int] = None
    genre_ids: Optional[list[int]] = None
    star_ids: Optional[list[int]] = None
    director_ids: Optional[list[int]] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                movie_update_schema_example
            ]
        }
    )


class MovieDeleteSchema(MovieBaseSchema):
    pass
