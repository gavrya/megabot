from app.shared.exceptions.app_error import AppError
from app.shared.exceptions.not_found_error import NotFoundError


def test_maps_to_404() -> None:
    error = NotFoundError()

    assert isinstance(error, AppError)
    assert (error.status_code, error.code) == (404, "not_found")
    assert error.message == "Requested resource does not exist."


def test_keeps_custom_message() -> None:
    assert NotFoundError("Article 1 not found").message == "Article 1 not found"
