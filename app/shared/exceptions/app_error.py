class AppError(Exception):
    """Base application error mapped to an HTTP response by the exception handlers."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or "Unexpected error"
        super().__init__(self.message)
