import json
from typing import Any, Tuple

from app.coarse_grain.models import BaseCoarseGrainModel, CoarseGrainModelRegistry, DynamicCoarseGrainModel
from app.settings import CITATIONS_DIR, MODELS_IMAGES_DIR, STATIC_DIR

RESIDUE_TYPE = {
    "A": "Purine",
    "G": "Purine",
    "C": "Pyrimidine",
    "U": "Pyrimidine",
}


class DocsContextBuilder:
    _citations_cache: dict[str, str] | None = None

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
    def get_model(cls, model_name: str, custom_model_data: dict | None = None) -> dict[str, Any]:  # type: ignore
        data = cls._build_model_data(model_name, custom_model_data)
        data.pop("raw_beads", None)
        return data

    @classmethod
    def _build_model_data(cls, model_name: str, custom_model_data: dict | None = None) -> dict[str, Any]:  # type: ignore
        model_cls, config = cls.load_model_config(model_name, custom_model_data)
        raw_beads = config.get("beads_per_residue", [])

        if not raw_beads and model_name == "custom":
            counts = set()
            for res_cfg in model_cls.nucleotides_config.values():
                counts.add(len(res_cfg.get("bead_names", {})))
            raw_beads = sorted(list(counts))
        image_name_for_url = None if model_name == "custom" else model_name

        model_data = {
            "id": model_name,
            "name": model_cls.name_verbose,
            "description": config.get(
                "description", f"Coarse-grained model: {model_cls.name_verbose}"
            ),
            "raw_beads": raw_beads,
            "beads": cls.format_beads(raw_beads),
            "citations": cls.format_citations(config),
            "mapping": cls.format_mapping(model_cls),
            "image_url": cls.get_image_url(image_name_for_url) or "",
        }
        return model_data

    @classmethod
    def load_model_config(cls, model_name: str, custom_model_data: dict[str, Any] | None = None) -> Tuple[BaseCoarseGrainModel, dict[str, Any]]:  # type: ignore
        if model_name == "custom":
            if custom_model_data is None:
                raise ValueError("Custom model selected but no data provided.")
            
            instance = DynamicCoarseGrainModel(custom_model_data)
            return instance, custom_model_data

        model_cls = CoarseGrainModelRegistry.get_model(model_name)
        model_instance = model_cls()
        data = model_instance.read_json_model()
        return model_instance, data  # type: ignore

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
    def load_citations(cls) -> dict[str, str]:
        if cls._citations_cache is None:
            with open(CITATIONS_DIR, "r", encoding="utf-8") as f:
                cls._citations_cache = json.load(f)
        return cls._citations_cache

    @classmethod
    def format_citations(cls, config: dict[str, Any]) -> list[str]:  # type: ignore
        citations_keys = config.get("citations", {})
        citations_values = cls.load_citations()

        citations = []
        for i, k in enumerate(citations_keys.values(), start=1):
            citations.append(f"{i}. {citations_values.get(k, k)}")

        return citations