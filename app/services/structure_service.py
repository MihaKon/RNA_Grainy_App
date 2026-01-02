from collections import defaultdict
from typing import Any, DefaultDict

from gemmi import Structure, cif, make_structure_from_block, read_pdb_string

from app.coarse_grain.parser import process_structure_with_coarse_grain_model
from app.models import COARSE_FILE_FORMAT, SupportedFormats
from app.coarse_grain.models import CoarseGrainModelRegistry


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
        initial_data = {
            "job_id": job_id,
            "reference_url": f"/api/jobs/{job_id}/reference?file_format={original_format.value}",
            "coarse_url": f"/api/jobs/{job_id}/coarse?file_format={COARSE_FILE_FORMAT.value}",
            "filename": filename,
            "file_format": [original_format.value, COARSE_FILE_FORMAT.value],
            "selected_model": CoarseGrainModelRegistry.get_model(selected_model).name_verbose,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)

        # fix: move to calculations in other issue
        """
        for structure in [original_structure, coarse_structure]:
            counts = count_structure_entities(structure)
            for key, count in counts.items():
                context[key].append(count)
        """
        return context
