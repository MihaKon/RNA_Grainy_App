from collections import Counter
from collections.abc import Iterator
from typing import Literal

from gemmi import Chain, EntityType, Model, Residue, Structure, cif

from app.coarse_grain.models import (
    EMPTY_ALTLOC,
    PRIMARY_ATOM_ALTLOC,
    BaseCoarseGrainModel,
    CalculateBeadModel,
    DynamicCoarseGrainModel,
)
from pdb_audit.issues import IssueContent, Issues
from pdb_audit.validation.context import ValidationContext

CANONICAL_RNA_RESIDUES = {"A", "C", "G", "U"}
CANONICAL_DNA_RESIDUES = {"DA", "DC", "DG", "DT"}


ResidueKey = tuple[int, str, str, str]
EntityCategory = Literal[
    "polymer",
    "non-polymer",
    "branched",
    "water",
    "unknown",
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


def get_structure_atom_count(structure: Structure) -> int:
    return sum(model.count_atom_sites() for model in structure)


def get_original_atom_counts_by_entity_type(content: str) -> Counter[str]:
    document = cif.read_string(content)
    block = document.sole_block()

    entity_types = {row[0]: row[1] for row in block.find("_entity.", ["id", "type"])}
    counts: Counter[str] = Counter()

    for row in block.find(
        "_atom_site.",
        ["label_entity_id"],
    ):
        entity_id = row[0]
        entity_type = entity_types.get(entity_id, "unknown")
        counts[entity_type] += 1

    return counts


def get_residue_entity_category(residue: Residue) -> EntityCategory:
    if residue.is_water() or residue.entity_type == EntityType.Water:
        return "water"

    if residue.entity_type == EntityType.Polymer:
        return "polymer"

    if residue.entity_type == EntityType.NonPolymer:
        return "non-polymer"

    if residue.entity_type == EntityType.Branched:
        return "branched"

    return "unknown"


def is_supported_polymer_residue(
    context: ValidationContext,
    residue: Residue,
) -> bool:
    return (
        residue.entity_type == EntityType.Polymer
        and residue.name in context.coarse_grain_model.nucleotides_config
    )


def get_parsed_atom_counts_by_entity_type(
    structure: Structure,
) -> Counter[str]:
    counts: Counter[str] = Counter()

    for _, _, residue in iter_residues(structure):
        category = get_residue_entity_category(residue)
        counts[category] += len(residue)

    return counts


def get_residue_key(
    model: Model,
    chain: Chain,
    residue: Residue,
) -> ResidueKey:
    return (
        model.num,
        chain.name,
        str(residue.seqid),
        residue.name,
    )


def get_bead_atom_names_for_residue(
    coarse_grain_model: BaseCoarseGrainModel, residue_name: str, bead_id: str
) -> list[str]:
    residue_config = coarse_grain_model.nucleotides_config[residue_name]
    bead_name = residue_config["bead_names"][bead_id]

    if isinstance(coarse_grain_model, DynamicCoarseGrainModel):
        atoms = residue_config["atom_centers"][bead_id]
        strategy = residue_config.get("strategies", {}).get(bead_id, "direct")

        if strategy == "direct":
            return atoms[:1]

        if strategy in ("geometric_center", "center_of_mass"):
            return atoms

        return []

    if isinstance(coarse_grain_model, CalculateBeadModel):
        return residue_config["atom_centers"][bead_id]

    return [bead_name]


def is_bead_constructible(
    coarse_grain_model: BaseCoarseGrainModel, residue: Residue, bead_id: str
) -> bool:
    atom_names = get_bead_atom_names_for_residue(
        coarse_grain_model=coarse_grain_model,
        residue_name=residue.name,
        bead_id=bead_id,
    )

    if not atom_names:
        return False

    available_atom_names = set()
    for atom in residue:
        if atom.altloc in (EMPTY_ALTLOC, PRIMARY_ATOM_ALTLOC):
            available_atom_names.add(atom.name)

    return not available_atom_names.isdisjoint(atom_names)


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
