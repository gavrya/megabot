from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.shared.dtos.error_response_dto import ErrorResponse
from app.shared.exceptions.app_error import AppError

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_body("validation_error", "Request validation failed", _details(exc)),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_body("http_error", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_body("internal_error", "Internal server error"),
        )


def _body(code: str, message: str, details: list[dict] | None = None) -> dict:
    return ErrorResponse(code=code, message=message, details=details).model_dump(exclude_none=True)


def _details(exc: RequestValidationError) -> list[dict]:
    return [
        {"field": ".".join(str(part) for part in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
