from app.shared.exceptions.app_error import AppError


class NotFoundError(AppError):
    """Requested resource does not exist."""

    status_code = 404
    code = "not_found"
