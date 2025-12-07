from collections import defaultdict
from typing import Any, DefaultDict

from app.coarse_grain.parser import CoarseGrainModels, transform_structure
from app.models import SupportedFormats, COARSE_FILE_FORMAT

from gemmi import Structure, cif, make_structure_from_block, read_pdb_string
from Bio.PDB import DSSP

class StructureProcessor:
    @staticmethod
    def parse_structure(
        content: str, file_format: SupportedFormats
    ) -> Structure:
        if file_format == SupportedFormats.CIF:
            dcif = cif.read_string(content)
            structure = make_structure_from_block(dcif.sole_block())
        else:
            structure = read_pdb_string(content)
        return structure

    @staticmethod
    def structure_to_string(structure: Structure, file_format: SupportedFormats) -> str:
        structure.setup_entities()
        structure.assign_label_seq_id()
        if file_format == SupportedFormats.PDB:
            return structure.make_pdb_string() 
        cif_doc = structure.make_mmcif_document()
        return cif_doc.as_string()

    @staticmethod
    def process_and_serialize_job(
        file_content: str, file_format: SupportedFormats, model_ids: list[int] | None,  chain_ids: list[str] | None, coarse_grain_model: CoarseGrainModels
    ) -> tuple[str,str]:
        reference_structure = StructureProcessor.parse_structure(file_content, file_format)

        reference_structure = transform_structure(reference_structure, model_ids=model_ids, chain_ids=chain_ids)
        coarse_structure = transform_structure(reference_structure, coarse_grain_model=coarse_grain_model)  
        
        reference_content = StructureProcessor.structure_to_string(reference_structure, file_format)
        coarse_content = StructureProcessor.structure_to_string(coarse_structure, COARSE_FILE_FORMAT)

        return reference_content, coarse_content
            
    @staticmethod
    def build_comparison_context(
        job_id: str,
        filename: str,
        file_format: SupportedFormats,
        selected_model: CoarseGrainModels
    ) -> DefaultDict[str, Any]:

        reference_format = file_format.normalize_format()
        initial_data = {
            "job_id": job_id,
            "reference_url": f"/api/jobs/{job_id}/reference?file_format={reference_format.value}", 
            "coarse_url": f"/api/jobs/{job_id}/coarse?file_format={COARSE_FILE_FORMAT.value}",
            "filename": filename,
            "file_format": [reference_format.value, COARSE_FILE_FORMAT.value],
            "selected_model": selected_model.name,
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
