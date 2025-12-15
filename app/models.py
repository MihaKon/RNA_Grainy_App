from enum import Enum

from fastapi import UploadFile
from pydantic import BaseModel, field_validator


class SupportedFormats(str, Enum):
    PDB = "pdb"
    CIF = "cif"
    MMCIF = "mmcif"

    def normalize_format(self) -> "SupportedFormats":
        if self == SupportedFormats.CIF:
            return SupportedFormats.MMCIF
        return self


COARSE_FILE_FORMAT = SupportedFormats.MMCIF


class UploadBase(BaseModel):
    selected_model: str


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
