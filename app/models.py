import json
from enum import Enum
from typing import Any

from Bio.PDB.MMCIFParser import MMCIFParser
from Bio.PDB.PDBParser import PDBParser
from fastapi import UploadFile
from pydantic import BaseModel, field_validator

from app.settings import COARSE_GRAIN_MODELS_DIR


class SupportedFormats(str, Enum):
    PDB = "pdb"
    CIF = "cif"


FORMAT_PARSERS = {
    SupportedFormats.PDB: PDBParser,
    SupportedFormats.CIF: MMCIFParser,
}


class CoarseGrainModels(Enum):
    DUMMY = "simrna.json"

    def model(self) -> dict[str, Any]:
        with open(COARSE_GRAIN_MODELS_DIR / self.value) as f:
            result = json.load(f)
        return result


class UploadBase(BaseModel):
    selected_model: CoarseGrainModels

    @field_validator("selected_model", mode="before")
    @classmethod
    def validate_model(cls, v):
        if isinstance(v, str):
            try:
                return CoarseGrainModels[v.upper()]
            except KeyError:
                valid_names = [e.name for e in CoarseGrainModels]
                raise ValueError(f"Invalid model: {v}. Must be one of {valid_names}")
        return v


class FileUploadRequest(UploadBase):
    file: UploadFile

    @field_validator("file")
    @classmethod
    def validate_file(cls, v):
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
    def validate_rcsb_id(cls, v):
        v = v.strip().upper()
        return v
