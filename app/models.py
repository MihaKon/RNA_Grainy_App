from __future__ import annotations

import json
import re
from enum import Enum

from fastapi import UploadFile
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


def is_letters_and_commas(text):
    pattern = r"[a-zA-Z,]+"

    return bool(re.fullmatch(pattern, text))


def is_numbers_and_commas(text):
    pattern = r"[\d,]+"

    return bool(re.fullmatch(pattern, text))


class UploadBase(BaseModel):
    selected_model: str
    custom_model_data: dict | str | None = None
    models: str | list[int]
    chains: str | list[str]

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

    @field_validator("models", mode="before")
    @classmethod
    def validate_models(cls, v: str | list | None) -> list[int]:
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, str):
            if not is_numbers_and_commas(v):
                raise ValueError("Incorrect symbols in the model selector.")
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        raise ValueError("models must be a string or list")

    @field_validator("chains", mode="before")
    @classmethod
    def validate_chains(cls, v: str | list | None) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not is_letters_and_commas(v):
                raise ValueError("Incorrect symbols in the chain selector.")
            return [x.strip() for x in v.split(",") if x.strip()]
        raise ValueError("chains must be a string or list")


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
