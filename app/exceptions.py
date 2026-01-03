from fastapi import Request
from pydantic import ValidationError
from app.messages import render_form_error_message

class AppException(Exception):
    pass

class FileProcessingError(AppException):
    pass

class ModelLoadingError(AppException):
    pass


async def app_exception_handler(request: Request, exc: Exception):
    error_message = str(exc)

    return render_form_error_message(
        request=request,
        error=error_message,
        status_code=400
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
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