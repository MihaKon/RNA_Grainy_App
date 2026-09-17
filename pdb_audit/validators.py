from dataclasses import dataclass, field
from pathlib import Path

from gemmi import Structure

from app.coarse_grain.models import CoarseGrainModelRegistry
from app.exceptions import FileProcessingError
from app.models.form import SupportedFormats
from app.services.structures import StructureProcessor
from pdb_audit.issues import IssueContent
from pdb_audit.validation.context import ValidationContext
from pdb_audit.validation.runner import (
    run_coarse_grain_checks,
    run_reference_checks,
)


@dataclass
class ValidatedCoarseGrainedStructure:
    structure: Structure
    issues: list[IssueContent] = field(default_factory=list)


@dataclass
class ValidatedStructure:
    file_name: str
    original_reference_cif: str
    reference_structure: Structure
    coarse_grain_results: dict[str, ValidatedCoarseGrainedStructure]
    reference_issues: list[IssueContent] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.reference_issues) or any(
            result.issues for result in self.coarse_grain_results.values()
        )


class Validator:
    def __init__(
        self,
        structures_path: Path,
        validated_structures: list[ValidatedStructure],
        file_format: SupportedFormats,
        models: list[int],
        chains: list[str],
    ) -> None:
        self.structures_path: Path = structures_path
        self.validated_structures = validated_structures
        self.file_format = file_format
        self.models = models
        self.chains = chains

    def validate(self) -> None:
        for item in self.validated_structures:
            reference_checked = False
            for model_name, result in item.coarse_grain_results.items():
                model_class = CoarseGrainModelRegistry.get_model(model_name)
                model = model_class()

                context = ValidationContext(
                    original_reference_cif=item.original_reference_cif,
                    reference_structure=item.reference_structure,
                    coarse_grain_structure=result.structure,
                    coarse_grain_model=model,
                )
                if not reference_checked:
                    item.reference_issues = run_reference_checks(context)
                    reference_checked = True
                result.issues = run_coarse_grain_checks(context)

    @classmethod
    def read_file(cls, structures_path: Path) -> str:
        try:
            file_content = structures_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise FileProcessingError(f"Error reading preset file: {e}")
        return file_content

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
    def parse_file(
        cls,
        structures_path: Path,
        file_format: SupportedFormats,
        coarse_grain_model: str | None,
        models: list[int],
        chains: list[str],
    ) -> "Validator":
        original_reference_cif = cls.read_file(structures_path)
        validated_structures: list[ValidatedStructure] = []

        reference_structure = cls.get_reference_structure(
            original_reference_cif, file_format, models, chains
        )
        coarse_grain_structures = cls.get_coarse_grain_structures(
            reference_structure, coarse_grain_model
        )

        coarse_grain_results: dict[str, ValidatedCoarseGrainedStructure] = {}
        for model_name, structure in coarse_grain_structures.items():
            coarse_grain_results[model_name] = ValidatedCoarseGrainedStructure(
                structure=structure,
            )

        validated_structures.append(
            ValidatedStructure(
                file_name=structures_path.stem,
                original_reference_cif=original_reference_cif,
                reference_structure=reference_structure,
                coarse_grain_results=coarse_grain_results,
            )
        )

        return cls(
            structures_path=structures_path,
            validated_structures=validated_structures,
            file_format=file_format,
            models=models,
            chains=chains,
        )
