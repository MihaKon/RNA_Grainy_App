from collections.abc import Callable

from pdb_audit.issues import IssueContent
from pdb_audit.validation.checks import (
    check_empty_models,
    check_invalid_number_of_aa_atoms,
    check_invalid_number_of_aa_atoms_by_entity_type,
    check_ligands_in_coarse_structure,
    check_nonpolymer_nucleotides_in_coarse_structure,
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
    check_ligands_in_coarse_structure,
    check_water_in_coarse_structure,
    check_nonpolymer_nucleotides_in_coarse_structure,
]

REFERENCE_CHECKS: list[CheckFunction] = [
    check_invalid_number_of_aa_atoms,
    check_invalid_number_of_aa_atoms_by_entity_type,
    check_reference_cif_entity_metadata_lost,
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
