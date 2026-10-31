import pytest
from pydantic import BaseModel, ValidationError

from app.shared.dtos.page_dto import Page


class _Item(BaseModel):
    name: str


def test_holds_typed_items() -> None:
    page = Page[_Item](items=[_Item(name="a")], total=3, limit=1, offset=0)

    assert page.model_dump() == {"items": [{"name": "a"}], "total": 3, "limit": 1, "offset": 0}


def test_validates_items_against_type_parameter() -> None:
    page = Page[_Item].model_validate(
        {"items": [{"name": "a"}], "total": 1, "limit": 20, "offset": 0}
    )
    assert isinstance(page.items[0], _Item)

    with pytest.raises(ValidationError):
        Page[_Item].model_validate({"items": [{"wrong": 1}], "total": 1, "limit": 20, "offset": 0})
