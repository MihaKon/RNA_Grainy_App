from collections.abc import Callable, Iterator
from dataclasses import dataclass

from gemmi import Chain, EntityType, Model, Residue, Structure

from app.coarse_grain.models import BaseCoarseGrainModel
from pdb_audit.models import IssueContent, Issues


@dataclass
class ValidationContext:
    reference_structure: Structure
    coarse_grain_structure: Structure
    coarse_grain_model: BaseCoarseGrainModel


CheckFunction = Callable[
    [ValidationContext],
    list[IssueContent],
]


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
            issues.append(
                IssueContent(
                    code=Issues.IONS_OR_LIGANDS_IN_COARSE_STRUCTURE.code,
                    model_index=model.num,
                    chain_name=chain.name,
                    seq_id=residue.seqid.num,
                    res_name=residue.name,
                )
            )
    return issues


CHECKS: list[CheckFunction] = [
    check_ions_or_ligands_in_coarse_grain_structure,
]


def run_checks(context: ValidationContext) -> list[IssueContent]:
    issues = []
    for check in CHECKS:
        issues.extend(check(context))

    return issues
