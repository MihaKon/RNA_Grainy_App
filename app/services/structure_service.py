from collections import defaultdict
from typing import Any, DefaultDict

from gemmi import Structure, cif, make_structure_from_block, read_pdb_string

from app.coarse_grain.parser import process_structure_with_coarse_grain_model
from app.models import COARSE_FILE_FORMAT, SupportedFormats
from app.coarse_grain.models import CoarseGrainModelRegistry
from app.exceptions import ModelLoadingError

class StructureProcessor:
    @staticmethod
    def parse_structure(content: str, file_format: SupportedFormats) -> Structure:
        if file_format == SupportedFormats.CIF:
            dcif = cif.read_string(content)
            structure = make_structure_from_block(dcif.sole_block())
        else:
            structure = read_pdb_string(content)
        return structure

    @staticmethod
    def apply_coarse_graining(structure: Structure, model: str) -> str:
        coarse_structure = process_structure_with_coarse_grain_model(structure, model)

        if COARSE_FILE_FORMAT == SupportedFormats.PDB:
            return coarse_structure.make_pdb_string()

        cif_doc = coarse_structure.make_mmcif_document()
        return cif_doc.as_string()

    @staticmethod
    def build_comparison_context(
        job_id: str,
        filename: str,
        file_format: SupportedFormats,
        selected_model: str,
    ) -> DefaultDict[str, Any]:
        original_format = file_format.normalize_format()
        
        model_cls = CoarseGrainModelRegistry.get_model(selected_model)
        
        model_instance = model_cls()
        try:
            model_config = model_instance.read_json_model()
        except Exception as e:
            raise ModelLoadingError(f"Failed to load model configuration: {e}")
            
        model_verbose_name = model_cls.name_verbose
        beads_per_residue = model_config.get("beads_per_residue", "Unknown")

        atom_mapping_display = {}
        raw_mapping = model_config.get("mapping", {})

        for group_name, group_data in raw_mapping.items():
            residues_list = group_data.get("residues", [])
            residues_str = ", ".join(residues_list)
            display_title = f"{group_name.capitalize()} ({residues_str})"

            descriptions = group_data.get("description", group_data.get("atoms", {}))
            
            atom_mapping_display[display_title] = descriptions

        description_text = model_config.get("description_text", f"Coarse-grained model: {model_verbose_name}")
        citation_text = model_config.get("citation", "Citation not available.")

        initial_data = {
            "reference_url": f"/api/jobs/{job_id}/reference?file_format={original_format.value}",
            "coarse_url": f"/api/jobs/{job_id}/coarse?file_format={COARSE_FILE_FORMAT.value}",
            "file_format": [original_format.value, COARSE_FILE_FORMAT.value],
            "job_id": job_id,
            "filename": filename,
            "selected_model": model_verbose_name,
            
            "atom_counts": {
                "original": "TODO: Count atoms",  
                "coarse": "TODO: Count beads",
            },
            "selected_chains": ["TODO"], 
            "selected_models": ["TODO"],
            
            "model_description": description_text,
            "model_citation": citation_text,
            "atom_mapping": atom_mapping_display,
            "beads_per_residue": beads_per_residue,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)
        return context