from enum import Enum

from fastapi import UploadFile
from pydantic import BaseModel, field_validator

from app.coarse_grain.models import CoarseGrainModels


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
    selected_model: CoarseGrainModels
    model_ids: list[int] | None = None
    chain_ids: list[str] | None = None

    @field_validator("selected_model", mode="before")
    @classmethod
    def validate_model(cls, v: str) -> CoarseGrainModels:
        try:
            return CoarseGrainModels[v.upper()]
        except KeyError:
            valid_names = [e.name for e in CoarseGrainModels]
            raise ValueError(f"Invalid model: {v}. Must be one of {valid_names}")

    @field_validator("model_ids", mode="before")
    @classmethod
    def validate_model_ids(cls, v: None | str | list[str]) -> list[int] | None:
        if v is None or (isinstance(v, str) and not v.strip()):
            return [0]
        if isinstance(v,str):
            v = v.split(",")
        if isinstance(v, list):
            ids = [int(x.strip()) for x in v if x.strip()] 
            if -1 in ids:
                return None
            return ids if ids else None         
        return v

    @field_validator("chain_ids", mode="before")
    @classmethod
    def validate_chain_ids(cls, v: None | str | list[str]) -> list[str] | None:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        if isinstance(v,str):
            v = v.split(",")
        if isinstance(v, list):
            chains = [str(item).strip() for item in v if str(item).strip()]
            return chains if chains else None
        return v
    

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
