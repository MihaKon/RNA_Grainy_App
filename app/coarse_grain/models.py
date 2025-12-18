from __future__ import annotations

import json
import pathlib
from abc import ABC

from gemmi import Selection, Structure

from app.settings import COARSE_GRAIN_MODELS_DIR


class CoarseGrainModelRegistry:
    """
    Singleton registry to store RNA model classes.
    """

    _registry: dict[str, type[BaseCoarseGrainModel]] = {}

    @classmethod
    def register(cls, model_cls: type[BaseCoarseGrainModel]):
        cls._registry[model_cls.__name__] = model_cls
        return model_cls

    @classmethod
    def get_model(cls, class_name: str) -> type[BaseCoarseGrainModel]:
        if class_name not in cls._registry:
            available = list(cls._registry.keys())
            raise KeyError(
                f"Model '{class_name}' not found. Available models: {available}"
            )
        return cls._registry[class_name]

    @classmethod
    def get_dropdown_options(cls) -> list[tuple[str, str]]:
        return sorted(
            [(key, model_cls.name_verbose) for key, model_cls in cls._registry.items()],
            key=lambda x: x[1],
        )


class BaseCoarseGrainModel(ABC):
    name_verbose: str
    JSON_model_file: pathlib.Path

    def __init__(self):
        self._cached_model_data: dict | None = None

    def read_json_model(self) -> dict:
        if self._cached_model_data is None:
            if not self.JSON_model_file or not self.JSON_model_file.exists():
                raise FileNotFoundError(f"Model file not found: {self.JSON_model_file}")

            with open(self.JSON_model_file, "r") as f:
                self._cached_model_data = json.load(f)

        assert self._cached_model_data is not None
        return self._cached_model_data

    def get_atoms_subset(self) -> list[str]:
        model_data = self.read_json_model()
        return model_data.get("atoms", [])

    def _get_selection_query(self) -> str:
        atoms_subset = self.get_atoms_subset()
        atoms = ",".join(atoms_subset) if atoms_subset else "*"
        query = f"//*//{atoms}"
        return query

    def get_coarse_grain_structure(self, original_structure: Structure) -> Structure:
        """Apply coarse-graining to the structure."""
        query = self._get_selection_query()
        selection = Selection(query)
        coarse_structure = selection.copy_structure_selection(original_structure)
        return coarse_structure


@CoarseGrainModelRegistry.register
class SimModel(BaseCoarseGrainModel):
    name_verbose: str = "SimRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "simrna.json"


@CoarseGrainModelRegistry.register
class NASTModel(BaseCoarseGrainModel):
    name_verbose: str = "NAST"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "nast.json"


@CoarseGrainModelRegistry.register
class YUPModel(BaseCoarseGrainModel):
    name_verbose: str = "YUP"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "yup.json"


@CoarseGrainModelRegistry.register
class Nares2PModel(BaseCoarseGrainModel):
    name_verbose: str = "Nares-2P"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / ".json"


@CoarseGrainModelRegistry.register
class IFoldRNAModel(BaseCoarseGrainModel):
    name_verbose: str = "iFoldRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "ifoldrna.json"


@CoarseGrainModelRegistry.register
class TopRNAModel(BaseCoarseGrainModel):
    name_verbose: str = "TopRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "toprna.json"


@CoarseGrainModelRegistry.register
class IsRNAOneModel(BaseCoarseGrainModel):
    name_verbose: str = "IsRNA1"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "is_rna_one.json"


@CoarseGrainModelRegistry.register
class IsRNATwoModel(BaseCoarseGrainModel):
    name_verbose: str = "IsRNA2"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "is_rna_two.json"


@CoarseGrainModelRegistry.register
class SPQRModel(BaseCoarseGrainModel):
    name_verbose: str = "SPQR"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "spqr.json"


@CoarseGrainModelRegistry.register
class MRNAModel(BaseCoarseGrainModel):
    name_verbose: str = "mRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / ".json"


@CoarseGrainModelRegistry.register
class HireModel(BaseCoarseGrainModel):
    name_verbose: str = "HireRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "hire_rna.json"


@CoarseGrainModelRegistry.register
class OxModel(BaseCoarseGrainModel):
    name_verbose: str = "oxRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "ox_rna.json"


@CoarseGrainModelRegistry.register
class FebModel(BaseCoarseGrainModel):
    name_verbose: str = "FebRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "feb_rna.json"


@CoarseGrainModelRegistry.register
class VFoldModel(BaseCoarseGrainModel):
    name_verbose: str = "VFold"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "v_fold.json"
