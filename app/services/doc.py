import json
from typing import Any, TypedDict

from app.coarse_grain.models import (
    BaseCoarseGrainModel,
    CoarseGrainModelRegistry,
    DynamicCoarseGrainModel,
)
from app.models.api import (
    BeadMapping,
    Citation,
    ModelDocumentation,
    ResidueMapping,
)
from app.settings import CITATIONS_DIR, MODELS_IMAGES_DIR, STATIC_DIR

RESIDUE_TYPE = {
    "A": "Purine",
    "G": "Purine",
    "C": "Pyrimidine",
    "U": "Pyrimidine",
}


class CitationData(TypedDict):
    text: str
    url: str


class DocsContextBuilder:
    _citations_cache: dict[str, CitationData] | None = None

    @classmethod
    def get_all_model_documentation(cls) -> list[ModelDocumentation]:
        models = [
            cls.get_model_documentation(model_name)
            for model_name in CoarseGrainModelRegistry._registry
        ]
        return sorted(
            models, key=lambda model: (model.beads_per_residue, model.name.lower())
        )

    @classmethod
    def get_model_documentation(
        cls, model_name: str, custom_model_data: dict | None = None
    ) -> ModelDocumentation:
        model, config = cls.load_model_config(model_name, custom_model_data)

        return ModelDocumentation(
            id=model_name,
            name=model.name_verbose,
            description=cls.get_description(model, config),
            beads_per_residue=cls.get_beads_per_residue(model_name, model, config),
            citations=cls.format_citations(config),
            mapping=cls.build_residue_mapping(model),
            image_url=cls.get_image_url(None if model_name == "custom" else model_name),
        )

    @classmethod
    def load_model_config(
        cls, model_name: str, custom_model_data: dict[str, Any] | None = None
    ) -> tuple[BaseCoarseGrainModel, dict[str, Any]]:  # type: ignore
        if model_name == "custom":
            if custom_model_data is None:
                raise ValueError("Custom model selected but no data provided.")

            instance = DynamicCoarseGrainModel(custom_model_data)
            return instance, custom_model_data

        model_cls = CoarseGrainModelRegistry.get_model(model_name)
        model_instance = model_cls()
        data = model_instance.read_json_model()
        return model_instance, data  # type: ignore

    @staticmethod
    def get_description(model: BaseCoarseGrainModel, config: dict[str, Any]) -> str:
        description: str = config.get(
            "description", f"Coarse-grained model: {model.name_verbose}"
        )
        return description

    @staticmethod
    def get_beads_per_residue(
        model_name: str,
        model: BaseCoarseGrainModel,
        config: dict[str, Any],
    ) -> list[int]:
        beads_per_residue: list[int] = config.get("beads_per_residue", [])

        if not beads_per_residue and model_name == "custom":
            beads_per_residue = sorted(
                {
                    len(residue_config.get("bead_names", {}))
                    for residue_config in model.nucleotides_config.values()
                }
            )

        return beads_per_residue

    @staticmethod
    def build_residue_mapping(model: BaseCoarseGrainModel) -> list[ResidueMapping]:
        residue_mappings = []

        for residue, residue_config in model.nucleotides_config.items():
            bead_names = residue_config.get("bead_names", {})
            descriptions = residue_config.get("description", {})

            residue_mappings.append(
                ResidueMapping(
                    residue=residue,
                    residue_type=RESIDUE_TYPE.get(residue, "Other"),
                    beads=[
                        BeadMapping(
                            bead_id=bead_id,
                            bead=bead_names[bead_id],
                            description=descriptions.get(bead_id, "-"),
                        )
                        for bead_id in sorted(bead_names)
                    ],
                )
            )

        return residue_mappings

    @classmethod
    def get_image_url(cls, model_name: str | None) -> str | None:
        if model_name is None:
            return None
        filename = f"{model_name.lower()}.png"
        relative_path = MODELS_IMAGES_DIR.relative_to(STATIC_DIR) / filename
        img_path = relative_path.as_posix()
        return f"/{STATIC_DIR.name}/{img_path}"

    @classmethod
    def load_citations(cls) -> dict[str, CitationData]:
        citations = cls._citations_cache

        if citations is None:
            with open(CITATIONS_DIR, encoding="utf-8") as file:
                citations = json.load(file)

            cls._citations_cache = citations

        return citations

    @classmethod
    def format_citations(cls, config: dict[str, Any]) -> list[Citation]:  # type: ignore
        citations_keys = config.get("citations", {})
        citations_values = cls.load_citations()

        citations: list[Citation] = []
        for number, citation_key in enumerate(citations_keys.values(), start=1):
            citation = citations_values[citation_key]

            citations.append(
                Citation(
                    number=number,
                    text=citation["text"],
                    url=citation["url"],
                )
            )

        return citations
