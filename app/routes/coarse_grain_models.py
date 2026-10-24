from fastapi import APIRouter, Form, status
from fastapi.responses import Response

from app.exceptions import InvalidModelParametersError
from app.models.api import ModelDocumentation
from app.models.form import parse_custom_model_json
from app.services.doc import DocsContextBuilder

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def list_models() -> list[ModelDocumentation]:
    return DocsContextBuilder.get_all_model_documentation()


@router.post("/custom/validate", status_code=status.HTTP_204_NO_CONTENT)
async def validate_custom_model(custom_model_data: str = Form(...)) -> Response:
    """Check a custom model definition without coarse-graining a structure."""
    try:
        parse_custom_model_json(custom_model_data)
    except ValueError as e:
        raise InvalidModelParametersError(str(e)) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)
