from fastapi import Request
from fastapi.responses import HTMLResponse
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

async def app_exception_handler(request: Request, exc: Exception) -> HTMLResponse:
    error_message = str(exc)

    return render_form_error_message(
        request=request,
        error=error_message,
        status_code=400
    )

async def validation_exception_handler(request: Request, exc: Exception) -> HTMLResponse:

    assert isinstance(exc, ValidationError)
    error_message = str(exc)
    try:
        first_error = exc.errors()[0]
        error_message = first_error.get("msg", str(exc))
        
        error_message = error_message.replace("Value error, ", "")
    except (IndexError, AttributeError):
        error_message = "Validation Error"

    return render_form_error_message(
        request=request,
        error=error_message,
        status_code=422
    )