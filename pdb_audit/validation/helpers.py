from collections.abc import Iterator

from gemmi import Chain, Model, Residue, Structure

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
