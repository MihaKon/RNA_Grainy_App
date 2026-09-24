from fastapi import APIRouter

from app.models.api import ModelDocumentation
from app.services.doc import DocsContextBuilder

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def list_models() -> list[ModelDocumentation]:
    return DocsContextBuilder.get_all_model_documentation()
