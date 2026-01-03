from typing import Any, Tuple
from app.coarse_grain.models import CoarseGrainModelRegistry

class ModelService:
    @classmethod
    def get_all_models(cls) -> list[dict[str, Any]]: # type: ignore
        models_data = []
        for model_name in CoarseGrainModelRegistry._registry.keys():
            models_data.append(cls._build_model_data(model_name))
            
        models_data.sort(key=lambda x: (x["raw_beads"], x["name"].lower()))

        for model in models_data:
            model.pop("raw_beads", None)

        return models_data

    @classmethod
    def get_model(cls, model_name: str) -> dict[str, Any]: # type: ignore
        data = cls._build_model_data(model_name)
        data.pop("raw_beads", None)
        return data

    @classmethod
    def _build_model_data(cls, model_name: str) -> dict[str, Any]: # type: ignore
        model_cls, config = cls.load_model_config(model_name)
        raw_beads = config.get("beads_per_residue", [])

        model_data = {
            "id": model_name,
            "name": model_cls.name_verbose,
            "description": config.get("description_text", f"Coarse-grained model: {model_cls.name_verbose}"),
            "raw_beads": raw_beads,
            "beads": cls.format_beads(raw_beads),
            "citation": cls.format_citations(config),
            "mapping": cls.format_mapping(config),
            "image_url": f"/static/images/models/{model_name.lower()}.png"
        }
        return model_data
    @classmethod
    def load_model_config(cls, model_name: str) -> Tuple[Any, dict[str, Any]]: # type: ignore
        model_cls = CoarseGrainModelRegistry.get_model(model_name)
        model_instance = model_cls()
        data = model_instance.read_json_model()
        return model_cls, data
    
    @classmethod
    def format_beads(cls, beads: list[int]) -> str: 
        return " or ".join(str(bead) for bead in beads)
    
    @classmethod
    def format_mapping(cls, config: dict[str, Any]) -> dict[str, Any]: # type: ignore
        formatted_mapping = {}
        raw_mapping = config.get("mapping", {})
        
        for group_key, group_data in raw_mapping.items():
            residues = ", ".join(group_data.get("residues", []))
            title = f"{group_key.capitalize()} ({residues})"
            details = group_data.get("atoms", group_data.get("description", {}))
            formatted_mapping[title] = details

        return formatted_mapping
    
    @classmethod
    def format_citations(cls, config: dict[str, Any]) -> list[str]: # type: ignore
        raw_citations = config.get("citation", {})
        citations = []
        for key in raw_citations.keys():
            text = raw_citations[key]
            citations.append(f"{key}. {text}")

        return citations
    

