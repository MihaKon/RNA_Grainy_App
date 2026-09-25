from dataclasses import dataclass

from gemmi import Structure

from app.coarse_grain.models import BaseCoarseGrainModel


@dataclass
class ValidationContext:
    file_name: str
    original_reference_cif: str
    reference_structure: Structure
    coarse_grain_structure: Structure
    coarse_grain_model: BaseCoarseGrainModel
