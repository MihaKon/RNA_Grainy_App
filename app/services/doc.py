import json
from typing import Any, TypedDict

from markupsafe import Markup, escape

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
    def get_all_models(cls) -> list[dict[str, Any]]:  # type: ignore
        models_data = []
        for model_name in CoarseGrainModelRegistry._registry.keys():
            models_data.append(cls._build_model_data(model_name))

        models_data.sort(key=lambda x: (x["raw_beads"], x["name"].lower()))

        for model in models_data:
            model.pop("raw_beads", None)

        return models_data

    @classmethod
    def get_model(
        cls, model_name: str, custom_model_data: dict | None = None
    ) -> dict[str, Any]:  # type: ignore
        data = cls._build_model_data(model_name, custom_model_data)
        data.pop("raw_beads", None)
        return data

    @classmethod
    def _build_model_data(
        cls, model_name: str, custom_model_data: dict | None = None
    ) -> dict[str, Any]:  # type: ignore
        model_cls, config = cls.load_model_config(model_name, custom_model_data)
        raw_beads = cls.get_beads_per_residue(model_name, model_cls, config)
        image_name_for_url = None if model_name == "custom" else model_name
        citations = cls.format_citations(config)
        description = cls.get_description(model_cls, config)

        model_data = {
            "id": model_name,
            "name": model_cls.name_verbose,
            "description": cls.format_description(description, citations),
            "raw_beads": raw_beads,
            "beads": cls.format_beads(raw_beads),
            "citations": citations,
            "mapping": cls.format_mapping(model_cls),
            "image_url": cls.get_image_url(image_name_for_url) or "",
        }
        return model_data

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
    def format_beads(cls, beads: list[int]) -> str:
        return " or ".join(str(bead) for bead in beads)

    @classmethod
    def format_mapping(cls, model_instance: BaseCoarseGrainModel) -> dict[str, Any]:  # type: ignore
        formatted_mapping: dict = {}
        raw_mapping = model_instance.nucleotides_config

        for res in raw_mapping.keys():
            row_data = []
            bead_names = raw_mapping[res].get("bead_names", {})
            descriptions = raw_mapping[res].get("description", {})

            for bead_id in sorted(bead_names.keys()):
                row_data.append(
                    {
                        "bead_id": bead_id,
                        "bead": bead_names[bead_id],
                        "description": descriptions.get(bead_id, "-"),
                    }
                )

            residue_type = RESIDUE_TYPE.get(res, "Other")
            if formatted_mapping.get(residue_type) is not None:
                formatted_mapping[residue_type].append(row_data)
            else:
                formatted_mapping[residue_type] = row_data

        return formatted_mapping

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

    @staticmethod
    def format_description(
        description: str,
        citations: list[Citation],
    ) -> Markup:
        formatted_description = str(escape(description))

        for citation in citations:
            marker = f"[{citation.number}]"

            link = Markup(
                '<a href="{}" '
                'target="_blank" '
                'rel="noopener noreferrer" '
                'class="text-accent hover:underline">'
                "{}</a>"
            ).format(
                citation.url,
                marker,
            )

            formatted_description = formatted_description.replace(
                marker,
                str(link),
            )

        return Markup(formatted_description)
