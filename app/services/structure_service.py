from collections import defaultdict
from typing import Any, DefaultDict

from gemmi import Structure, cif, make_structure_from_block, read_pdb_string

from app.coarse_grain.parser import process_structure_with_coarse_grain_model
from app.models import COARSE_FILE_FORMAT, SupportedFormats
from app.services.doc_builder import ModelContextBuilder

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
        
        model_data = ModelContextBuilder.get_model(selected_model)

        initial_data = {
            "reference_url": f"/api/jobs/{job_id}/reference?file_format={original_format.value}",
            "coarse_url": f"/api/jobs/{job_id}/coarse?file_format={COARSE_FILE_FORMAT.value}",
            "file_format": [original_format.value, COARSE_FILE_FORMAT.value],
            "job_id": job_id,
            "filename": filename,
            
            "atom_counts": {
                "original": "TODO: Count atoms",  
                "coarse": "TODO: Count beads",
            },
            "selected_chains": ["TODO"], 
            "selected_models": ["TODO"],
            
            "model": model_data,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)
        return context