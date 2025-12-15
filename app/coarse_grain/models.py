from __future__ import annotations

import json
import pathlib
from typing import Protocol

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
    def get_model(cls, class_name: str) -> type[BaseCoarseGrainModel] | None:
        return cls._registry.get(class_name)

    @classmethod
    def get_dropdown_options(cls) -> list[tuple[str, str]]:
        options = []
        for key, model_cls in cls._registry.items():
            dummy_instance = model_cls()
            options.append((key, dummy_instance.name_verbose))

        return sorted(options, key=lambda x: x[1])


class BaseCoarseGrainModel(Protocol):
    name_verbose: str
    JSON_model_file: pathlib.Path

    def filter_atoms(self) -> None:
        raise NotImplementedError()

    def add_connections(self) -> None:
        raise NotImplementedError

    def read_json_model(self) -> None:
        raise NotImplementedError

    def save_structure(self) -> None:
        raise NotImplementedError


@CoarseGrainModelRegistry.register
class SimModel(BaseCoarseGrainModel):
    name_verbose: str = "SimRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "simrna.json"


@CoarseGrainModelRegistry.register
class NASTModel(BaseCoarseGrainModel):
    name_verbose: str = "NAST"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class YUPModel(BaseCoarseGrainModel):
    name_verbose: str = "YUP"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class Nares2PModel(BaseCoarseGrainModel):
    name_verbose: str = "Nares-2P"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class IFoldRNAModel(BaseCoarseGrainModel):
    name_verbose: str = "iFoldRNA"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class TopRNAModel(BaseCoarseGrainModel):
    name_verbose: str = "TopRNA"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class IsRNAOneModel(BaseCoarseGrainModel):
    name_verbose: str = "IsRNA1"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class IsRNATwoModel(BaseCoarseGrainModel):
    name_verbose: str = "IsRNA2"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class SPQRModel(BaseCoarseGrainModel):
    name_verbose: str = "SPQR"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class MRNAModel(BaseCoarseGrainModel):
    name_verbose: str = "mRNA"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class HireModel(BaseCoarseGrainModel):
    name_verbose: str = "HireRNA"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class OxModel(BaseCoarseGrainModel):
    name_verbose: str = "oxRNA"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class FebModel(BaseCoarseGrainModel):
    name_verbose: str = "FebRNA"
    JSON_model_file: pathlib.Path = ""


@CoarseGrainModelRegistry.register
class VFoldModel(BaseCoarseGrainModel):
    name_verbose: str = "VFold"
    JSON_model_file: pathlib.Path = ""
