from enum import Enum

from fastapi import UploadFile
from pydantic import BaseModel, field_validator

from app.coarse_grain.models import CoarseGrainModels


class SupportedFormats(str, Enum):
    PDB = "pdb"
    CIF = "cif"

class UploadBase(BaseModel):
    selected_model: CoarseGrainModels

    @field_validator("selected_model", mode="before")
    @classmethod
    def validate_model(cls, v: str) -> CoarseGrainModels:
        try:
            return CoarseGrainModels[v.upper()]
        except KeyError:
            valid_names = [e.name for e in CoarseGrainModels]
            raise ValueError(f"Invalid model: {v}. Must be one of {valid_names}")


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
