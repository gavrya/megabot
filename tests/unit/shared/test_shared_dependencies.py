from typing import get_args

from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.shared.dependencies import PageParamsDep, SessionDep
from app.shared.dtos.page_params_dto import PageParams


def test_session_dep_resolves_request_session() -> None:
    session_type, marker = get_args(SessionDep)

    assert session_type is AsyncSession
    assert isinstance(marker, Depends)
    assert marker.dependency is get_session


def test_page_params_dep_builds_from_query() -> None:
    params_type, marker = get_args(PageParamsDep)

    assert params_type is PageParams
    assert isinstance(marker, Depends)
    assert marker.dependency is None
