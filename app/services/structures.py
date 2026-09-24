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
from app.models.form import SupportedFormats


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
