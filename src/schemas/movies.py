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
    star_schema_example,
)


class GenreBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": genre_schema_example})


class GenreCreateSchema(GenreBaseSchema):
    pass


class GenreUpdateSchema(GenreBaseSchema):
    id: int


class GenreDeleteSchema(GenreBaseSchema):
    id: int


class GenreReadSchema(GenreBaseSchema):
    id: int
    movie_count: Optional[int] = Field(None, examples=[12])

    model_config = ConfigDict(from_attributes=True)


class StarBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": star_schema_example})


class StarCreateSchema(StarBaseSchema):
    pass


class StarUpdateSchema(StarBaseSchema):
    id: int


class StarDeleteSchema(StarBaseSchema):
    id: int


class StarReadSchema(StarBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DirectorBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": director_schema_example})


class DirectorCreateSchema(DirectorBaseSchema):
    pass


class DirectorUpdateSchema(DirectorBaseSchema):
    id: int


class DirectorDeleteSchema(DirectorBaseSchema):
    id: int


class DirectorReadSchema(DirectorBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CertificationBaseSchema(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": certification_schema_example})


class CertificationCreateSchema(CertificationBaseSchema):
    pass


class CertificationUpdateSchema(CertificationBaseSchema):
    id: int


class CertificationDeleteSchema(CertificationBaseSchema):
    id: int


class CertificationReadSchema(CertificationBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": movie_item_schema_example})


class MovieDetailSchema(MovieBaseSchema):
    id: int
    genres: list[GenreBaseSchema]
    stars: list[StarBaseSchema]
    directors: list[DirectorBaseSchema]

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": movie_detail_schema_example})


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    time: int

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": movie_item_schema_example})


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": movie_list_response_schema_example})


class MovieCreateSchema(MovieBaseSchema):
    genre_ids: list[int]
    star_ids: list[int]
    director_ids: list[int]

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": movie_create_schema_example})


class MovieUpdateSchema(MovieCreateSchema):
    pass


class MovieDeleteSchema(MovieBaseSchema):
    pass
