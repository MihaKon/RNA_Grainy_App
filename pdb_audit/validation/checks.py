from gemmi import EntityType, cif

from pdb_audit.issues import IssueContent, Issues
from pdb_audit.validation.context import ValidationContext
from pdb_audit.validation.helpers import (
    get_structure_atom_count,
    iter_residues,
    make_issue,
)


def check_ions_or_ligands_in_coarse_grain_structure(
    context: ValidationContext,
) -> list[IssueContent]:
    issues = []
    for model, chain, residue in iter_residues(context.coarse_grain_structure):
        if residue.entity_type == EntityType.NonPolymer or residue.is_water():
            issues.append(
                make_issue(
                    issue=Issues.IONS_OR_LIGANDS_IN_COARSE_STRUCTURE,
                    model=model,
                    chain=chain,
                    residue=residue,
                )
            )
    return issues


def check_invalid_number_of_aa_atoms(context: ValidationContext) -> list[IssueContent]:
    original_reference_cif = cif.read_string(context.original_reference_cif)
    original_reference_block = original_reference_cif.sole_block()

    original_atom_count = len(original_reference_block.find_values("_atom_site.id"))
    parsed_atom_count = get_structure_atom_count(context.reference_structure)
    if original_atom_count == parsed_atom_count:
        return []

    return [
        make_issue(
            Issues.INVALID_NUMBER_OF_AA_ATOMS,
            details=f"Raw CIF contains {original_atom_count} atoms, "
            f"StructureProcessor returns {parsed_atom_count}",
        )
    ]
