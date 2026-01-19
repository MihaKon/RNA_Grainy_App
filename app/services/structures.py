from collections import defaultdict
from typing import Any, DefaultDict

from fastapi import Request
from gemmi import (
    MmcifOutputGroups,
    PdbWriteOptions,
    Structure,
    cif,
    make_structure_from_block,
    read_pdb_string,
)

from app.coarse_grain.parser import process_structure_with_coarse_grain_model
from app.models import COARSE_FILE_FORMAT, SupportedFormats
from app.services.doc import DocsContextBuilder


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
        return process_structure_with_coarse_grain_model(structure, model)
    
    @staticmethod
    def structure_to_pdb_string(structure: Structure) -> str:
        options = PdbWriteOptions()
        return structure.make_pdb_string(options=options)
    @staticmethod
    def structure_to_cif_string(structure: Structure) -> str:
        groups = MmcifOutputGroups(False)
        groups.entry = True
        groups.title_keywords = True
        groups.conn = True
        groups.cell = True
        groups.atoms = True
        cif_doc = structure.make_mmcif_document(groups=groups)
        return cif_doc.as_string()
    

    @staticmethod
    def build_comparison_context(
        request: Request,
        job_id: str,
        filename: str,
        file_format: SupportedFormats,
        selected_model: str,
    ) -> DefaultDict[str, Any]:
        original_format = file_format.normalize_format()

        model_data = DocsContextBuilder.get_model(selected_model)

        reference_url = str(
            request.url_for(
                "get_job_file", job_id=job_id, file_type="reference"
            ).include_query_params(file_format=original_format.value)
        )
        coarse_mmcif_url = str(
            request.url_for(
                "get_job_file", job_id=job_id, file_type="coarse"
            ).include_query_params(file_format=COARSE_FILE_FORMAT.value)
        )

        coarse_pdb_url = str(
            request.url_for(
                "get_job_file", job_id=job_id, file_type="coarse"
            ).include_query_params(file_format=SupportedFormats.PDB.value)
        )

        initial_data = {
            "reference_url": reference_url,
            "coarse_mmcif_url": coarse_mmcif_url,
            "coarse_pdb_url": coarse_pdb_url,
            "file_format": [original_format.value, COARSE_FILE_FORMAT.value],
            "job_id": job_id,
            "filename": filename,
            "atom_counts": {
                "original": "TODO: Count atoms",
                "coarse": "TODO: Count beads",
                "reduction": "TODO: Compute reduction",
            },
            "selected_chains": ["TODO"],
            "selected_models": ["TODO"],
            "model": model_data,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)
        return context
