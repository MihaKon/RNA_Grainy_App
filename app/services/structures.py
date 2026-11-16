from gemmi import (
    Structure,
    cif,
    make_structure_from_block,
    read_pdb_string,
)

from app.coarse_grain.models import EMPTY_ALTLOC, PRIMARY_ATOM_ALTLOC
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
    def get_coarse_structure_atom_count(structure: Structure) -> int:
        atom_counts = structure[0].count_atom_sites()
        return atom_counts

    @staticmethod
    def get_rna_atom_count(
        original_structure: Structure, coarse_structure: Structure
    ) -> int:
        mapped_residue_keys = {
            (chain.name, str(residue.seqid), residue.name)
            for chain in coarse_structure[0]
            for residue in chain
            if len(residue) > 0
        }

        modified_residue_parents = {
            (
                modification.chain_name,
                str(modification.res_id.seqid),
                modification.res_id.name,
            ): modification.parent_comp_id
            for modification in original_structure.mod_residues
        }

        atom_count = 0

        for chain in original_structure[0]:
            for residue in chain:
                residue_key = (chain.name, str(residue.seqid), residue.name)
                parent_residue_key = (
                    chain.name,
                    str(residue.seqid),
                    modified_residue_parents.get(residue_key, residue.name),
                )

                if (
                    residue_key not in mapped_residue_keys
                    and parent_residue_key not in mapped_residue_keys
                ):
                    continue

                atom_count += sum(
                    atom.altloc in (EMPTY_ALTLOC, PRIMARY_ATOM_ALTLOC)
                    for atom in residue
                )

        return atom_count

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
