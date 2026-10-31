import pytest
from pydantic import ValidationError

from app.shared.dtos.page_params_dto import PageParams


def test_defaults() -> None:
    params = PageParams()

    assert (params.limit, params.offset) == (20, 0)


@pytest.mark.parametrize(("limit", "offset"), [(1, 0), (100, 0), (20, 10_000)])
def test_accepts_bounds(limit: int, offset: int) -> None:
    assert PageParams(limit=limit, offset=offset).limit == limit


@pytest.mark.parametrize(("limit", "offset"), [(0, 0), (101, 0), (20, -1)])
def test_rejects_out_of_range(limit: int, offset: int) -> None:
    with pytest.raises(ValidationError):
        PageParams(limit=limit, offset=offset)
