from gemmi import EntityType, cif

from app.services.structures import StructureProcessor
from pdb_audit.issues import IssueContent, Issues
from pdb_audit.validation.context import ValidationContext
from pdb_audit.validation.helpers import (
    get_original_atom_counts_by_entity_type,
    get_parsed_atom_counts_by_entity_type,
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
    original_reference_cif = cif.read_string(
        context.original_reference_cif
    ).sole_block()

    original_atom_count = len(original_reference_cif.find_values("_atom_site.id"))
    parsed_atom_count = get_structure_atom_count(context.reference_structure)
    if original_atom_count == parsed_atom_count:
        return []

    return [
        make_issue(
            Issues.INVALID_NUMBER_OF_AA_ATOMS,
            details=f"Raw CIF contains {original_atom_count} atoms. StructureProcessor returns {parsed_atom_count}. Skipped {original_atom_count - parsed_atom_count} atoms.",
        )
    ]


def check_invalid_number_of_aa_atoms_by_entity_type(
    context: ValidationContext,
) -> list[IssueContent]:
    original_counts = get_original_atom_counts_by_entity_type(
        context.original_reference_cif
    )
    parsed_counts = get_parsed_atom_counts_by_entity_type(context.reference_structure)

    categories = set(original_counts) | set(parsed_counts)

    differences = {}

    for category in categories:
        if original_counts[category] != parsed_counts[category]:
            differences[category] = {
                "original": original_counts[category],
                "parsed": parsed_counts[category],
            }

    if not differences:
        return []

    return [
        make_issue(
            issue=Issues.INVALID_NUMBER_OF_AA_ATOMS_BY_ENTITY_TYPE,
            details=f"Differences by entity type: \n {differences}",
        )
    ]


def check_reference_cif_entity_metadata_lost(
    context: ValidationContext,
) -> list[IssueContent]:
    original_block = cif.read_string(context.original_reference_cif).sole_block()

    serialized_cif = StructureProcessor.structure_to_cif_string(
        context.reference_structure
    )
    serialized_block = cif.read_string(serialized_cif).sole_block()

    required_tags = (
        "_entity.id",
        "_entity.type",
        "_entity_poly.entity_id",
        "_entity_poly.type",
        "_struct_asym.id",
        "_struct_asym.entity_id",
        "_atom_site.label_entity_id",
    )

    missing_tags = []

    for tag in required_tags:
        if original_block.find_values(tag) and not serialized_block.find_values(tag):
            missing_tags.append(tag)

    if not missing_tags:
        return []

    return [
        make_issue(
            Issues.REFERENCE_CIF_ENTITY_METADATA_LOST,
            details=f"Missing mmCIF tags after serialization: {', '.join(missing_tags)}",
        )
    ]
