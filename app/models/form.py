from __future__ import annotations

import json
import re
from enum import StrEnum

from fastapi import UploadFile
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from app.coarse_grain.models import CoarseGrainModelRegistry
from app.models.custom_model import CustomModelDefinition
from app.settings import ALLOWED_PRESET_IDS, JSON_MAX_CHARS, JSON_MAX_UPLOAD_SIZE


class SupportedFormats(StrEnum):
    PDB = "pdb"
    CIF = "cif"
    MMCIF = "mmcif"

    def normalize_format(self) -> SupportedFormats:
        if self == SupportedFormats.CIF:
            return SupportedFormats.MMCIF
        return self


COARSE_FILE_FORMAT = SupportedFormats.MMCIF


def is_numbers_and_commas(text: str) -> bool:
    pattern = r"[\d,\s]+"

    return bool(re.fullmatch(pattern, text))


def is_numbers_letters_and_commas(text: str) -> bool:
    pattern = r"^[a-zA-Z0-9,\s]*$"

    return bool(re.fullmatch(pattern, text))


CUSTOM_MODEL_ID = "custom"


def describe_custom_model_error(error: ValidationError) -> str:
    first_error = error.errors()[0]
    message = str(first_error["msg"]).removeprefix("Value error, ")
    path = ".".join(str(part) for part in first_error["loc"])
    return f"Invalid custom model: {f'{path}: ' if path else ''}{message}"


class UploadBase(BaseModel):
    selected_model: str
    custom_model_data: dict | str | None = None
    models: str | list[int]
    chains: str | list[str]

    @field_validator("selected_model")
    @classmethod
    def validate_selected_model(cls, v: str) -> str:
        if v != CUSTOM_MODEL_ID and v not in CoarseGrainModelRegistry._registry:
            raise ValueError(f"Unknown coarse-grained model: {v}.")
        return v

    @model_validator(mode="after")
    def require_custom_model_data(self) -> UploadBase:
        if self.selected_model == CUSTOM_MODEL_ID and self.custom_model_data is None:
            raise ValueError("Custom model selected but no definition was provided.")
        return self

    @field_validator("custom_model_data", mode="before")
    @classmethod
    def validate_json_structure(cls, v: str | None) -> dict | None:
        if not v or (isinstance(v, str) and v.strip() == ""):
            return None

        if isinstance(v, str):
            if len(v.encode("utf-8")) > JSON_MAX_UPLOAD_SIZE:
                raise ValueError("Custom model JSON upload size is too large.")
            if len(v) > JSON_MAX_CHARS:
                raise ValueError("Custom model JSON is too large.")
            try:
                data = json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format.")
        else:
            data = v

        try:
            CustomModelDefinition.model_validate(data)
        except ValidationError as e:
            raise ValueError(describe_custom_model_error(e))
        return data

    @field_validator("models", mode="before")
    @classmethod
    def validate_models(cls, v: str | list | None) -> list[int]:
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [int(x) for x in v if int(x) > 0]
        if isinstance(v, str):
            if not is_numbers_and_commas(v):
                raise ValueError(
                    "Incorrect symbols in the model selector or provided model ID is negative."
                )
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        raise ValueError("Models must be a string or list")

    @field_validator("chains", mode="before")
    @classmethod
    def validate_chains(cls, v: str | list | None) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not is_numbers_letters_and_commas(v):
                raise ValueError("Incorrect symbols in the chain selector.")
            return [x.strip() for x in v.split(",") if x.strip()]
        raise ValueError("Chains must be a string or list")


class FileUploadRequest(UploadBase):
    file: UploadFile

    @field_validator("file")
    @classmethod
    def validate_file(cls, v: UploadFile) -> UploadFile:
        if not v.filename:
            raise ValueError("No file provided")
        ext = v.filename.split(".")[-1].lower()
        try:
            SupportedFormats(ext)
        except ValueError:
            raise ValueError("Unsupported file format.")
        return v


class RCSBRequest(UploadBase):
    rcsb_id: str

    @field_validator("rcsb_id")
    def validate_rcsb_id(cls, v: str) -> str:
        v = v.strip().upper()
        return v


class PresetRequest(UploadBase):
    preset_id: str

    @field_validator("preset_id")
    def validate_preset_id(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in ALLOWED_PRESET_IDS:
            raise ValueError("Invalid example ID.")
        return v
