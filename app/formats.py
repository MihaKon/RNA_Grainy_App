from __future__ import annotations
from enum import Enum

class SupportedFormats(str, Enum):
    PDB = "pdb"
    CIF = "cif"
    MMCIF = "mmcif"

    def normalize_format(self) -> SupportedFormats:
        if self == SupportedFormats.CIF:
            return SupportedFormats.MMCIF
        return self


COARSE_FILE_FORMAT = SupportedFormats.MMCIF