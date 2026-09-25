import re
from collections import defaultdict
from typing import Any

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
from app.models.form import COARSE_FILE_FORMAT, SupportedFormats
from app.services.doc import DocsContextBuilder

_REFERENCE_MMCIF_CATEGORIES = (
    "_entity.",
    "_chem_comp.",
    "_pdbx_struct_mod_residue.",
)


def _base_mmcif_groups() -> MmcifOutputGroups:
    groups = MmcifOutputGroups(False)
    groups.atoms = True
    groups.group_pdb = True
    groups.entry = True
    groups.title_keywords = True
    groups.cell = True
    groups.conn = True
    groups.atoms = True
    groups.entity = True
    groups.entity_poly = True
    groups.struct_asym = True
    return groups


def _base_pdb_options(minimal: bool) -> PdbWriteOptions:
    options = PdbWriteOptions(minimal=minimal)
    options.preserve_serial = True
    options.conect_records = True
    options.link_records = False
    return options


def _fix_mmcif_entry_id(
    block: cif.Block,
    structure: Structure,
    filename: str | None,
    coarse: bool,
    model_name: str | None = None,
) -> None:
    raw_id = block.find_value("_entry.id")
    entry_id = cif.as_string(raw_id).strip() if raw_id is not None else ""

    candidates = (entry_id, filename or "", structure.name, block.name)
    base_name = next(
        (
            value.strip()
            for value in candidates
            if value and value.strip() not in ("", "?", ".")
        ),
        "RNAgrainy",
    )
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", base_name).strip("_")
    safe_name = safe_name or "RNAgrainy"

    if coarse:
        safe_model_name = (
            re.sub(r"[^A-Za-z0-9_-]+", "_", model_name or "coarse_grained").strip("_")
            or "coarse_grained"
        )

        coarse_id = f"{safe_name}_{safe_model_name}"
        block.name = coarse_id
        block.set_pair("_entry.id", coarse_id)
    elif entry_id in ("", "?", "."):
        block.set_pair("_entry.id", safe_name)
        block.name = safe_name


def _fix_pdb_header_and_title(
    pdb_structure: Structure,
    pdb_content: str,
    filename: str | None,
    model_name: str | None,
    source_content: str | None,
    source_format: SupportedFormats | None,
) -> str:
    prefix: list[str] = []
    header = None

    if source_format == SupportedFormats.PDB and source_content is not None:
        header = next(
            (line for line in source_content.splitlines() if line.startswith("HEADER")),
            None,
        )
    elif source_format in (SupportedFormats.CIF, SupportedFormats.MMCIF):
        generated_headers = pdb_structure.make_pdb_string(
            options=PdbWriteOptions(headers_only=True)
        )
        header = next(
            (
                line
                for line in generated_headers.splitlines()
                if line.startswith("HEADER")
            ),
            None,
        )

    if header is not None:
        prefix.append(header)

    if model_name is not None:
        entry_id = (
            pdb_structure.info["_entry.id"].strip()
            if "_entry.id" in pdb_structure.info
            else ""
        )
        base_name = (
            entry_id if entry_id not in ("", "?", ".") else filename or "RNAgrainy"
        )
        prefix.append(f"TITLE     {base_name}_{model_name}")

    return "\n".join(prefix) + "\n" + pdb_content if prefix else pdb_content


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
    def parse_structure(
        content: str,
        file_format: SupportedFormats,
        models: list[int],
        chains: list[str],
    ) -> Structure:
        if file_format == SupportedFormats.CIF or file_format == SupportedFormats.MMCIF:
            dcif = cif.read_string(content)
            structure = make_structure_from_block(dcif.sole_block())
        else:
            structure = read_pdb_string(content)
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
    def structure_to_pdb_string(
        structure: Structure,
        minimal_metadata: bool,
        filename: str | None = None,
        model_name: str | None = None,
        source_content: str | None = None,
        source_format: SupportedFormats | None = None,
    ) -> str:
        pdb_structure = structure.clone()
        write_options = _base_pdb_options(minimal=minimal_metadata)

        if minimal_metadata:
            write_options.cryst1_record = False
            write_options.end_record = True

        pdb_structure.shorten_chain_names()
        pdb_content = pdb_structure.make_pdb_string(options=write_options)

        if not minimal_metadata:
            return pdb_content

        return _fix_pdb_header_and_title(
            pdb_structure,
            pdb_content,
            filename,
            model_name,
            source_content,
            source_format,
        )

    @staticmethod
    def coarse_structure_to_cif_string(
        structure: Structure,
        model_name: str,
        filename: str | None = None,
    ) -> str:
        groups = _base_mmcif_groups()
        groups.title_keywords = False
        groups.cell = False
        groups.entity_poly_seq = True

        document = structure.make_mmcif_document(groups=groups)
        _fix_mmcif_entry_id(
            document.sole_block(),
            structure,
            filename,
            coarse=True,
            model_name=model_name,
        )
        return document.as_string()

    @staticmethod
    def reference_structure_to_cif_string(
        structure: Structure,
        source_content: str,
        filename: str,
    ) -> str:
        groups = _base_mmcif_groups()
        groups.entity_poly_seq = True
        groups.chem_comp = True

        document = structure.make_mmcif_document(groups=groups)
        target_block = document.sole_block()
        source_block = cif.read_string(source_content).sole_block()

        for category in _REFERENCE_MMCIF_CATEGORIES:
            source_data = source_block.get_mmcif_category(category, raw=True)
            if source_data:
                target_block.set_mmcif_category(
                    category,
                    source_data,
                    raw=True,
                )

        _fix_mmcif_entry_id(
            target_block,
            structure,
            filename,
            coarse=False,
        )
        return document.as_string()

    @staticmethod
    def build_comparison_context(
        request: Request,
        workspace_id: str,
        filename: str,
        file_format: SupportedFormats,
        selected_model: str,
        atom_counts: dict[str, int],
        selected_models: list[int],
        selected_chains: list[str],
        custom_model_data: dict | None = None,
    ) -> defaultdict[str, Any]:
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
                "get_result_file", workspace_id=workspace_id, file_type="reference"
            ).include_query_params(file_format=original_format.value)
        )
        coarse_mmcif_url = str(
            request.url_for(
                "get_result_file", workspace_id=workspace_id, file_type="coarse"
            ).include_query_params(file_format=COARSE_FILE_FORMAT.value)
        )

        coarse_pdb_url = str(
            request.url_for(
                "get_result_file", workspace_id=workspace_id, file_type="coarse"
            ).include_query_params(file_format=SupportedFormats.PDB.value)
        )

        consumed_url = str(
            request.url_for(
                "mark_result_as_consumed",
                workspace_id=workspace_id,
            )
        )

        initial_data = {
            "reference_url": reference_url,
            "coarse_mmcif_url": coarse_mmcif_url,
            "coarse_pdb_url": coarse_pdb_url if is_pdb_available else None,
            "consumed_url": consumed_url,
            "file_format": [original_format.value, COARSE_FILE_FORMAT.value],
            "workspace_id": workspace_id,
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

        context: defaultdict[str, Any] = defaultdict(list, initial_data)
        return context
