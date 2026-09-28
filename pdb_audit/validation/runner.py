from collections.abc import Callable

from pdb_audit.issues import IssueContent
from pdb_audit.validation.checks import (
    check_alt_loc_present,
    check_bead_missing_despite_available_source_atoms,
    check_bead_skipped_due_to_missing_source_atoms,
    check_connectivity_between_invalid_beads,
    check_connectivity_not_found,
    check_connectivity_with_not_existent_bead,
    check_dna_residues_in_coarse_structure,
    check_duplicated_connectivity,
    check_empty_chains,
    check_empty_models,
    check_excessive_connectivity_length,
    check_invalid_number_of_aa_atoms,
    check_invalid_number_of_aa_atoms_by_entity_type,
    check_ligands_and_ions_in_coarse_structure,
    check_missing_modified_residue,
    check_nucleotides_are_marked_as_polymer,
    check_protein_residues_in_coarse_structure,
    check_reference_cif_entity_metadata_lost,
    check_water_in_coarse_structure,
    check_wrong_connectivity_type,
)
from pdb_audit.validation.context import ValidationContext

CheckFunction = Callable[
    [ValidationContext],
    list[IssueContent],
]


COARSE_GRAIN_CHECKS: list[CheckFunction] = [
    check_protein_residues_in_coarse_structure,
    check_empty_models,
    check_ligands_and_ions_in_coarse_structure,
    check_water_in_coarse_structure,
    check_nucleotides_are_marked_as_polymer,
    check_dna_residues_in_coarse_structure,
    check_empty_chains,
    check_bead_skipped_due_to_missing_source_atoms,
    check_bead_missing_despite_available_source_atoms,
    check_connectivity_with_not_existent_bead,
    check_duplicated_connectivity,
    check_wrong_connectivity_type,
    check_connectivity_not_found,
    check_excessive_connectivity_length,
    check_connectivity_between_invalid_beads,
    check_missing_modified_residue,
]

REFERENCE_CHECKS: list[CheckFunction] = [
    check_invalid_number_of_aa_atoms,
    check_invalid_number_of_aa_atoms_by_entity_type,
    check_reference_cif_entity_metadata_lost,
    check_alt_loc_present,
]


def run_checks(
    context: ValidationContext,
    checks: list[CheckFunction],
) -> list[IssueContent]:
    issues = []

    for check in checks:
        issues.extend(check(context))

    return issues


def run_reference_checks(
    context: ValidationContext,
) -> list[IssueContent]:
    return run_checks(context, REFERENCE_CHECKS)


def run_coarse_grain_checks(
    context: ValidationContext,
) -> list[IssueContent]:
    return run_checks(context, COARSE_GRAIN_CHECKS)
