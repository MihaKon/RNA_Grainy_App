from __future__ import annotations

from enum import Enum

from fastapi import UploadFile
import json
from pydantic import BaseModel, field_validator

from app.json_validation import CustomModelDefinition


class SupportedFormats(str, Enum):
    PDB = "pdb"
    CIF = "cif"
    MMCIF = "mmcif"

    def normalize_format(self) -> SupportedFormats:
        if self == SupportedFormats.CIF:
            return SupportedFormats.MMCIF
        return self


COARSE_FILE_FORMAT = SupportedFormats.MMCIF


class UploadBase(BaseModel):
    selected_model: str
    custom_model_data: dict | None = None

    @field_validator("custom_model_data", mode="before")
    @classmethod
    def validate_json_structure(cls, v: str | dict | None) -> dict | None:
        if not v or (isinstance(v, str) and v.strip() == ""):
            return None
        
        if isinstance(v, str):
            try:
                data = json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format.")
        else:
            data = v
        
        try:
            CustomModelDefinition.model_validate(data)
            return data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format.")
        except Exception as e:
            raise ValueError(f"Invalid Custom Model structure: {e}")

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

class ExampleRequest(UploadBase):
    example_id: str

    @field_validator("example_id")
    def validate_example_id(cls, v: str) -> str:
        v = v.strip()
        return v