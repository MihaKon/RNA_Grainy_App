from collections.abc import Callable, Iterator
from dataclasses import dataclass

from gemmi import Chain, EntityType, Model, Residue, Structure

from app.coarse_grain.models import BaseCoarseGrainModel
from pdb_audit.models import IssueContent, Issues


@dataclass
class ValidationContext:
    original_reference_cif: str
    reference_structure: Structure
    coarse_grain_structure: Structure
    coarse_grain_model: BaseCoarseGrainModel


def iter_models(structure: Structure) -> Iterator[Model]:
    yield from structure


def iter_chains(structure: Structure) -> Iterator[tuple[Model, Chain]]:
    for model in structure:
        for chain in model:
            yield model, chain


def iter_residues(structure: Structure) -> Iterator[tuple[Model, Chain, Residue]]:
    for model in structure:
        for chain in model:
            for residue in chain:
                yield model, chain, residue


def check_ions_or_ligands_in_coarse_grain_structure(
    context: ValidationContext,
) -> list[IssueContent]:
    issues = []
    for model, chain, residue in iter_residues(context.coarse_grain_structure):
        if residue.entity_type == EntityType.NonPolymer or residue.is_water():
            issue = Issues.IONS_OR_LIGANDS_IN_COARSE_STRUCTURE
            issues.append(
                IssueContent.from_issue(
                    issue=issue,
                    model_index=model.num,
                    chain_name=chain.name,
                    seq_id=residue.seqid.num,
                    res_name=residue.name,
                )
            )
    return issues


CheckFunction = Callable[
    [ValidationContext],
    list[IssueContent],
]


COARSE_GRAIN_CHECKS: list[CheckFunction] = [
    check_ions_or_ligands_in_coarse_grain_structure,
]

REFERENCE_CHECKS: list[CheckFunction] = []


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
