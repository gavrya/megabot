from app.shared.exceptions.app_error import AppError


class ConflictError(AppError):
    """Requested change conflicts with the current state."""

    status_code = 409
    code = "conflict"
