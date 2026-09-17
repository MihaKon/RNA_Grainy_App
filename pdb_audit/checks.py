from collections.abc import Callable, Iterator
from dataclasses import dataclass

from gemmi import Chain, EntityType, Model, Residue, Structure, cif

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


def get_structure_atom_count(structure: Structure) -> int:
    return sum(model.count_atom_sites() for model in structure)


def make_issue(
    issue: Issues,
    model: Model | None = None,
    chain: Chain | None = None,
    residue: Residue | None = None,
    details: str | None = None,
) -> IssueContent:
    content = IssueContent.from_issue(
        issue=issue,
        model_index=model.num if model is not None else None,
        chain_name=chain.name if chain is not None else None,
        seq_id=residue.seqid.num if residue is not None else None,
        res_name=residue.name if residue is not None else None,
    )

    if details:
        content.message = f"{content.message}. {details}"

    return content


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
