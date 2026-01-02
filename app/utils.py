from typing import Any, Dict
from app.coarse_grain.models import CoarseGrainModelRegistry
from app.exceptions import ValidationError
import re

def sort_key_func(k):
    match = re.search(r'\d+', str(k))
    return int(match.group()) if match else 0


def get_model_info(model_name: str) -> Dict[str, Any]: # type: ignore
    try:
        model_cls = CoarseGrainModelRegistry.get_model(model_name)
    except ValueError:
        raise ValidationError(f"Model '{model_name}' not found in registry.")

    model_instance = model_cls()
    try:
        config = model_instance.read_json_model()
    except Exception as e:
        raise ValidationError(f"Failed to load model configuration for {model_name}: {e}")

    formatted_mapping = {}
    raw_mapping = config.get("mapping", {})
    
    for group_key, group_data in raw_mapping.items():
        residues = ", ".join(group_data.get("residues", []))
        title = f"{group_key.capitalize()} ({residues})"
        
        details = group_data.get("atoms", group_data.get("description", {}))
        formatted_mapping[title] = details

    raw_citations = config.get("citation", {})
    citations = []
    sorted_keys = sorted(raw_citations.keys(), key=sort_key_func)
    for key in sorted_keys:
        text = raw_citations[key]
        full_citation = f"{key} {text}"
        citations.append(full_citation)

    return {
        "id": model_name,
        "name": model_cls.name_verbose,
        "description": config.get("description_text", f"Coarse-grained model: {model_cls.name_verbose}"),
        "citation": citations, 
        "beads_per_residue": config.get("beads_per_residue", "Unknown"),
        "mapping": formatted_mapping,
        "image_url": f"/static/images/models/{model_name.lower()}.png"
    }