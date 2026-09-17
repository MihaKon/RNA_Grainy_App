from collections import Counter
from collections.abc import Iterator

from gemmi import Chain, EntityType, Model, Residue, Structure, cif

from pdb_audit.issues import IssueContent, Issues


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


def get_parsed_atom_counts_by_entity_type(structure: Structure) -> Counter[str]:
    counts: Counter[str] = Counter()
    for model, chain, residue in iter_residues(structure):
        atom_count = len(residue)
        if residue.is_water():
            counts["water"] += atom_count
        elif residue.entity_type == EntityType.Polymer:
            counts["polymer"] += atom_count
        elif residue.entity_type == EntityType.NonPolymer:
            counts["non-polymer"] += atom_count
        else:
            counts["unknown"] += atom_count
    return counts


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
