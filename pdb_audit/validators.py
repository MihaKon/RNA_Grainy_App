from dataclasses import dataclass, field
from pathlib import Path

from gemmi import (
    Structure,
)

from app.coarse_grain.models import CoarseGrainModelRegistry
from app.exceptions import FileProcessingError
from app.models.form import SupportedFormats
from app.services.structures import StructureProcessor
from pdb_audit.checks import ValidationContext, run_checks
from pdb_audit.models import IssueContent


@dataclass
class CoarseGrainStructureValidation:
    structure: Structure
    issues: list[IssueContent] = field(default_factory=list)


@dataclass
class ValidatedStructure:
    file_name: str
    reference_structure: Structure
    coarse_grain_results: dict[str, CoarseGrainStructureValidation]


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

    def validate(self) -> None:
        for item in self.structures:
            for model_name, result in item.coarse_grain_results.items():
                model_class = CoarseGrainModelRegistry.get_model(model_name)
                model = model_class()

                context = ValidationContext(
                    reference_structure=item.reference_structure,
                    coarse_grain_structure=result.structure,
                    coarse_grain_model=model,
                )
                result.issues.extend(run_checks(context))

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
        validated_structures: list[ValidatedStructure] = []

        for path, content in zip(structures_paths, structures_contents):
            reference_structure = cls.get_reference_structure(
                content, file_format, models, chains
            )
            coarse_grain_structures = cls.get_coarse_grain_structures(
                reference_structure, coarse_grain_model
            )

            coarse_grain_results: dict[str, CoarseGrainStructureValidation] = {}
            for model_name, structure in coarse_grain_structures.items():
                coarse_grain_results[model_name] = CoarseGrainStructureValidation(
                    structure=structure,
                )

            validated_structures.append(
                ValidatedStructure(
                    file_name=path.stem,
                    reference_structure=reference_structure,
                    coarse_grain_results=coarse_grain_results,
                )
            )

        return cls(
            structures_paths=structures_paths,
            validated_structures=validated_structures,
            file_format=file_format,
            models=models,
            chains=chains,
        )
