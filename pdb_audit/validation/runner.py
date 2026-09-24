from collections.abc import Callable

from pdb_audit.issues import IssueContent
from pdb_audit.validation.checks import (
    check_alt_loc_present,
    check_dna_residues_in_coarse_structure,
    check_empty_chains,
    check_empty_models,
    check_invalid_number_of_aa_atoms,
    check_invalid_number_of_aa_atoms_by_entity_type,
    check_ligands_and_ions_in_coarse_structure,
    check_nucleotides_are_marked_as_polymer,
    check_protein_residues_in_coarse_structure,
    check_reference_cif_entity_metadata_lost,
    check_water_in_coarse_structure,
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
