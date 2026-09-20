class AppError(Exception):
    """Base application error mapped to an HTTP response by the exception handlers."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or "Unexpected error"
        super().__init__(self.message)


class NotFoundError(AppError):
    """Requested resource does not exist."""

    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    """Requested change conflicts with the current state."""

    status_code = 409
    code = "conflict"
