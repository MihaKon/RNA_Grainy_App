from fastapi import APIRouter

from app.models.api import AppConfig
from app.models.form import SupportedFormats
from app.settings import (
    ALLOWED_PRESET_IDS,
    JSON_MAX_CHARS,
    JSON_MAX_UPLOAD_SIZE,
    MAX_FILE_UPLOAD_SIZE,
)

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
async def get_app_config() -> AppConfig:
    return AppConfig(
        supported_file_formats=[file_format.value for file_format in SupportedFormats],
        preset_ids=sorted(ALLOWED_PRESET_IDS),
        max_file_upload_size=MAX_FILE_UPLOAD_SIZE,
        custom_model_json_max_chars=JSON_MAX_CHARS,
        custom_model_json_max_size=JSON_MAX_UPLOAD_SIZE,
    )
