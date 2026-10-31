from app.shared.dtos.error_response_dto import ErrorResponse


def test_details_are_optional() -> None:
    error = ErrorResponse(code="not_found", message="Missing")

    assert error.details is None
    assert error.model_dump(exclude_none=True) == {"code": "not_found", "message": "Missing"}


def test_keeps_details() -> None:
    details = [{"field": "title", "message": "Field required"}]

    error = ErrorResponse(code="validation_error", message="Invalid", details=details)

    assert error.model_dump()["details"] == details
