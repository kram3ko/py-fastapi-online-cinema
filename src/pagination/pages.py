from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar, cast

from fastapi import Query
from fastapi_pagination.bases import AbstractPage, AbstractParams, RawParams
from pydantic import BaseModel, Field

T = TypeVar("T")


class Params(BaseModel, AbstractParams):
    page: int = Query(1, ge=1, description="Page number")
    size: int = Query(10, ge=1, le=20, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=(self.page - 1) * self.size,
        )


class Page(AbstractPage[T], Generic[T]):
    results: list[T]
    total_items: int
    total_pages: int
    next_page: str | None = Field(
        default=None, examples=["/url_path/?page=1&size=10"]
    )
    prev_page: str | None = Field(
        default=None, examples=["/url_path/?page=3&size=10"]
    )

    __params_type__ = Params

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        **kwargs: Any,
    ) -> Page[T]:
        params = cast(Params, params)
        total = kwargs.get("total")
        url = kwargs.get("url")
        assert total is not None, "total_items must be provided"
        assert url is not None, "url must be provided"

        total_pages = (total + params.size - 1) // params.size

        return cls(
            results=list(items),
            total_items=total,
            total_pages=total_pages,
            next_page=f"{url}?page={params.page + 1}&size={params.size}"
            if params.page < total_pages
            else None,
            prev_page=f"{url}?page={params.page - 1}&size={params.size}"
            if params.page > 1
            else None,
        )
