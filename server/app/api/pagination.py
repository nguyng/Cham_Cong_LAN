from typing import Annotated, Callable, TypeVar

from fastapi import Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


class Pagination:
    """Optional pagination that keeps older list-only clients compatible."""

    def __init__(
        self,
        page: int | None = Query(default=None, ge=1),
        page_size: int = Query(default=50, ge=1, le=200),
    ):
        self.page = page
        self.page_size = page_size


Page = Annotated[Pagination, Depends()]
T = TypeVar("T")


def paginated(
    db: Session,
    query: Select,
    pagination: Pagination,
    serializer: Callable[[T], dict] = lambda item: item,
):
    """Return a legacy list, or an item/metadata envelope when ``page`` is supplied."""
    if pagination.page is None:
        return [serializer(item) for item in db.scalars(query).unique().all()]

    total = db.scalar(
        select(func.count()).select_from(query.order_by(None).limit(None).offset(None).subquery())
    )
    items = (
        db.scalars(
            query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
        )
        .unique()
        .all()
    )
    pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)
    return {
        "items": [serializer(item) for item in items],
        "pagination": {
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
            "pages": pages,
        },
    }


def paginated_rows(rows: list[dict], pagination: Pagination):
    if pagination.page is None:
        return rows
    total = len(rows)
    start = (pagination.page - 1) * pagination.page_size
    return {
        "items": rows[start : start + pagination.page_size],
        "pagination": {
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
            "pages": max(1, (total + pagination.page_size - 1) // pagination.page_size),
        },
    }
