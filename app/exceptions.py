from collections.abc import Sequence
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class AppException(Exception):
    pass


class InvalidRequestError(AppException):
    """Exception raised for invalid requests."""

    pass


class FileProcessingError(AppException):
    """Exception raised for errors during file processing."""

    pass


class ModelLoadingError(AppException):
    """Exception raised for errors during model loading."""

    pass


class InvalidModelParametersError(AppException):
    """Exception raised for invalid model parameters."""

    pass


def error_response(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": message}
    )


def describe_validation_error(errors: Sequence[Any]) -> str:
    first_error = errors[0]
    error_type = first_error.get("type", "")
    field_path = first_error.get("loc", [])
    field_name = str(field_path[-1]) if field_path else "field"

    if error_type == "value_error":
        return str(first_error.get("msg", "")).removeprefix("Value error, ")

    error_map = {
        "extra_forbidden": f"Unexpected field: {field_name}",
        "missing": f"Required: {field_name}",
        "type_error": f"Invalid type for {field_name}. ",
    }

    error_message = error_map.get(error_type)
    if not error_message:
        for key in error_map:
            if error_type.startswith(key):
                error_message = error_map[key]
                break

    return error_message or f"Invalid {field_name}"


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(str(exc))


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if isinstance(exc, ValidationError | RequestValidationError):
        return error_response(describe_validation_error(exc.errors()))
    return error_response(str(exc).split("Value error, ")[-1])
