from collections.abc import Callable

from pdb_audit.issues import IssueContent
from pdb_audit.validation.checks import (
    check_invalid_number_of_aa_atoms,
    check_ions_or_ligands_in_coarse_grain_structure,
)
from pdb_audit.validation.context import ValidationContext

CheckFunction = Callable[
    [ValidationContext],
    list[IssueContent],
]


COARSE_GRAIN_CHECKS: list[CheckFunction] = [
    check_ions_or_ligands_in_coarse_grain_structure,
]

REFERENCE_CHECKS: list[CheckFunction] = [check_invalid_number_of_aa_atoms]


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
