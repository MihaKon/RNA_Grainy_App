from fastapi import Request
from fastapi.responses import HTMLResponse

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


async def app_exception_handler(request: Request, exc: Exception) -> HTMLResponse:
    error_message = str(exc)

    return render_form_error_message(
        request=request, error=error_message, status_code=422
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> HTMLResponse:
    if isinstance(exc, ValueError):
        first_error = exc.errors()[0]  # type: ignore
        error_type = first_error.get("type", "")
        field_path = first_error.get("loc", [])
        field_name = str(field_path[-1]) if field_path else "field"

        error_map = {
            "extra_forbidden": f"Unexpected field: {field_name}",
            "missing": f"Required: {field_name}",
            "value_error": f"Invalid value for {field_name}. Check data types and structure.",
            "type_error": f"Invalid type for {field_name}. ",
        }

        error_message = error_map.get(error_type)
        if not error_message:
            for key in error_map:
                if error_type.startswith(key):
                    error_message = error_map[key]
                    break
        if not error_message:
            error_message = f"Invalid {field_name}"
    else:
        error_message = str(exc).split("Value error, ")[-1]

    return render_form_error_message(
        request=request, error=error_message, status_code=422
    )
