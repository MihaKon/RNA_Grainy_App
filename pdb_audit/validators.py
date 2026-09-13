from dataclasses import dataclass
from pathlib import Path

from gemmi import (
    Structure,
)

from app.coarse_grain.models import CoarseGrainModelRegistry
from app.exceptions import FileProcessingError
from app.models.form import SupportedFormats
from app.services.structures import StructureProcessor


@dataclass
class ValidatedStructure:
    file_name: str
    reference_structure: Structure
    coarse_grain_structures: dict[str, Structure]


class Validator:
    def __init__(
        self,
        structures_paths: list[Path],
        validated_structures: list[ValidatedStructure],
        file_format: SupportedFormats,
        models: list[int],
        chains: list[str],
    ) -> None:
        self.structures_paths: list[Path] = structures_paths
        self.structures = validated_structures
        self.file_format = file_format
        self.models = models
        self.chains = chains

    @classmethod
    def read_files(cls, structures_paths: list[Path]) -> list[str]:
        contents = []
        for path in structures_paths:
            try:
                file_content = path.read_text(encoding="utf-8")
                contents.append(file_content)
            except UnicodeDecodeError as e:
                raise FileProcessingError(f"Error reading preset file: {e}")
        return contents

    @classmethod
    def get_reference_structure(
        cls,
        structures_content: str,
        file_format: SupportedFormats,
        models: list[int],
        chains: list[str],
    ) -> Structure:
        reference_structure = StructureProcessor.parse_structure(
            structures_content, file_format, models=models, chains=chains
        )
        return reference_structure

    @classmethod
    def get_coarse_grain_structures(
        cls,
        reference_structure: Structure,
        coarse_grain_model: str | None,
    ) -> dict[str, Structure]:
        cg_models = {}

        if coarse_grain_model:
            cg_models[coarse_grain_model] = StructureProcessor.apply_coarse_graining(
                reference_structure, coarse_grain_model, None
            )
        else:
            for model in CoarseGrainModelRegistry._registry.keys():
                cg_models[model] = StructureProcessor.apply_coarse_graining(
                    reference_structure, model, None
                )

        return cg_models

    @classmethod
    def parse_files(
        cls,
        structures_paths: list[Path],
        file_format: SupportedFormats,
        coarse_grain_model: str | None,
        models: list[int],
        chains: list[str],
    ) -> "Validator":
        structures_contents = cls.read_files(structures_paths)
        validated_structures = []

        for path, content in zip(structures_paths, structures_contents):
            reference_structure = cls.get_reference_structure(
                content, file_format, models, chains
            )
            coarse_grain_structures = cls.get_coarse_grain_structures(
                reference_structure, coarse_grain_model
            )
            validated_structures.append(
                ValidatedStructure(
                    file_name=path.stem,
                    reference_structure=reference_structure,
                    coarse_grain_structures=coarse_grain_structures,
                )
            )

        return cls(
            structures_paths=structures_paths,
            validated_structures=validated_structures,
            file_format=file_format,
            models=models,
            chains=chains,
        )
