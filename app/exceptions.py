from collections.abc import Sequence
from typing import Any

from fastapi import Request, status
from fastapi.exception_handlers import (
    request_validation_exception_handler as default_request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from app.messages import render_form_error_message


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


API_PATH_PREFIX = "/api/"


def is_api_request(request: Request) -> bool:
    return request.url.path.startswith(API_PATH_PREFIX)


def error_response(request: Request, message: str) -> Response:
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT

    if is_api_request(request):
        return JSONResponse(status_code=status_code, content={"detail": message})

    return render_form_error_message(
        request=request, error=message, status_code=status_code
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


async def app_exception_handler(request: Request, exc: Exception) -> Response:
    return error_response(request, str(exc))


async def validation_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, ValidationError):
        error_message = describe_validation_error(exc.errors())
    else:
        error_message = str(exc).split("Value error, ")[-1]

    return error_response(request, error_message)


async def request_validation_exception_handler(
    request: Request, exc: Exception
) -> Response:
    if is_api_request(request) and isinstance(exc, RequestValidationError):
        return error_response(request, describe_validation_error(exc.errors()))

    return await default_request_validation_exception_handler(request, exc)  # type: ignore[arg-type]
