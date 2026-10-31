from app.shared.exceptions.app_error import AppError


class _DocumentedError(AppError):
    """Documented failure."""


class _UndocumentedError(AppError):
    pass


def test_defaults_to_internal_error() -> None:
    error = AppError("boom")

    assert (error.status_code, error.code, error.message) == (500, "internal_error", "boom")
    assert str(error) == "boom"


def test_message_falls_back_to_docstring() -> None:
    assert _DocumentedError().message == "Documented failure."


def test_message_falls_back_to_generic_text() -> None:
    assert _UndocumentedError().message == "Unexpected error"
