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
from app.exceptions import AppException
from app.formats import COARSE_FILE_FORMAT, SupportedFormats
from app.services.doc import DocsContextBuilder


def filter_structure_inplace(
    structure: Structure, models: list[int], chains: list[str]
) -> None:
    if models:
        for i in range(len(structure) - 1, -1, -1):
            if structure[i].num not in models:
                del structure[i]

    if chains:
        for model in structure:
            for i in range(len(model) - 1, -1, -1):
                if model[i].name not in chains:
                    del model[i]


class StructureProcessor:
    @staticmethod
    def get_structure_atom_count(structure: Structure) -> int:
        atom_counts = structure[0].count_atom_sites()
        return atom_counts

    @staticmethod
    def read_structure_from_file(
        content: str, file_format: SupportedFormats
    ) -> Structure:
        if file_format == SupportedFormats.CIF or file_format == SupportedFormats.MMCIF:
            dcif = cif.read_string(content)
            structure = make_structure_from_block(dcif.sole_block())
        else:
            structure = read_pdb_string(content)
        return structure

    @staticmethod
    def parse_structure(
        content: str,
        file_format: SupportedFormats,
        models: list[int],
        chains: list[str],
    ) -> Structure:
        structure = StructureProcessor.read_structure_from_file(content, file_format)
        filter_structure_inplace(structure, models, chains)
        if not structure or not len(structure) or not len(structure[0]):
            raise AppException(
                "Provided structure after filtration is empty. Check selected models and chains."
            )
        return structure

    @staticmethod
    def apply_coarse_graining(
        structure: Structure, model: str, custom_model_data: dict | None = None
    ) -> Structure:
        return process_structure_with_coarse_grain_model(
            structure, model, custom_model_data
        )

    @staticmethod
    def structure_to_pdb_string(structure: Structure) -> str:
        write_options = PdbWriteOptions(preserve_serial=True, conect_records=True)
        write_options.link_records = False
        structure.shorten_chain_names()
        return structure.make_pdb_string(options=write_options)

    @staticmethod
    def structure_to_cif_string(structure: Structure) -> str:
        groups = MmcifOutputGroups(False)
        groups.entry = True
        groups.title_keywords = True
        groups.conn = True
        groups.cell = True
        groups.atoms = True
        groups.assembly = True
        cif_doc = structure.make_mmcif_document(groups=groups)
        return cif_doc.as_string()

    @staticmethod
    def build_comparison_context(
        request: Request,
        job_id: str,
        filename: str,
        file_format: SupportedFormats,
        selected_model: str,
        atom_counts: dict[str, int],
        selected_models: list[int],
        selected_chains: list[str],
        custom_model_data: dict | None = None,
    ) -> DefaultDict[str, Any]:
        original_format = file_format.normalize_format()

        model_data = DocsContextBuilder.get_model(selected_model, custom_model_data)
        original_atom_count = atom_counts["original"]
        coarse_atom_count = atom_counts["coarse"]
        is_pdb_available = coarse_atom_count <= 99999
        reduction = (
            1 - (coarse_atom_count / original_atom_count)
            if original_atom_count > 0
            else 0
        )

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

        coarse_reconstructed_pdb_url = str(
            request.url_for(
                "get_job_file", job_id=job_id, file_type="coarse_reconstructed"
            ).include_query_params(file_format=SupportedFormats.PDB.value)
        )

        initial_data = {
            "reference_url": reference_url,
            "coarse_mmcif_url": coarse_mmcif_url,
            "coarse_pdb_url": coarse_pdb_url if is_pdb_available else None,
            "coarse_reconstructed_pdb_url": coarse_reconstructed_pdb_url
            if is_pdb_available
            else None,
            "file_format": [
                original_format.value,
                COARSE_FILE_FORMAT.value,
                SupportedFormats.PDB.value,
            ],
            "job_id": job_id,
            "filename": filename,
            "atom_counts": {
                "original": original_atom_count,
                "coarse": coarse_atom_count,
                "reduction": f"{reduction:.2%}",
            },
            "selected_chains": selected_chains,
            "selected_models": selected_models,
            "model": model_data,
            "is_pdb_available": is_pdb_available,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)
        return context
