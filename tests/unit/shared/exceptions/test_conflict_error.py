from app.shared.exceptions.app_error import AppError
from app.shared.exceptions.conflict_error import ConflictError


def test_maps_to_409() -> None:
    error = ConflictError()

    assert isinstance(error, AppError)
    assert (error.status_code, error.code) == (409, "conflict")
    assert error.message == "Requested change conflicts with the current state."


def test_keeps_custom_message() -> None:
    assert ConflictError("Title taken").message == "Title taken"
