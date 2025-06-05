from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from schemas.examples.movies import (
    genre_schema_example,
    star_schema_example,
    director_schema_example,
    certification_schema_example,
    movie_item_schema_example,
    movie_list_response_schema_example,
    movie_create_schema_example,
    movie_detail_schema_example,
    movie_update_schema_example
)


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
    id: int


class GenreDeleteSchema(GenreBaseSchema):
    id: int


class GenreReadSchema(GenreBaseSchema):
    id: int
    movie_count: Optional[int] = Field(None, example=12)

    class Config:
        orm_mode = True


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
    id: int


class StarDeleteSchema(StarBaseSchema):
    id: int


class StarReadSchema(StarBaseSchema):
    id: int

    class Config:
        orm_mode = True


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
    id: int


class DirectorDeleteSchema(DirectorBaseSchema):
    id: int


class DirectorReadSchema(DirectorBaseSchema):
    id: int

    class Config:
        orm_mode = True


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
    id: int


class CertificationDeleteSchema(CertificationBaseSchema):
    id: int


class CertificationReadSchema(CertificationBaseSchema):
    id: int

    class Config:
        orm_mode = True


class MovieBaseSchema(BaseModel):
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
    genres: List[GenreBaseSchema]
    stars: List[StarBaseSchema]
    directors: List[DirectorBaseSchema]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                movie_detail_schema_example
            ]
        }
    )


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    time: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                movie_item_schema_example
            ]
        }
    )


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
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


class MovieCreateSchema(MovieBaseSchema):
    genre_ids: List[int]
    star_ids: List[int]
    director_ids: List[int]

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
    genre_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None

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
