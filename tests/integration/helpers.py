import re
from html import unescape

from gemmi import Structure

# chain_index, residue_seqid, residue_name, atom_name
AtomKey = tuple[int, str, str, str]

# element_name, x, y, z
AtomData = tuple[str, float, float, float]


def extract_data_attribute(html: str, attribute: str) -> str:
    match = re.search(rf'{attribute}="([^"]+)"', html)

    if match is None:
        raise AssertionError(f"Missing HTML attribute: {attribute}")

    return unescape(match.group(1))


def get_atoms(
    structure: Structure,
) -> tuple[dict[AtomKey, AtomData], dict[int, AtomKey]]:
    assert len(structure) == 1, "This test expects one selected model"

    atoms: dict[AtomKey, AtomData] = {}
    serial_to_key: dict[int, AtomKey] = {}

    for chain_index, chain in enumerate(structure[0]):
        for residue in chain:
            for atom in residue:
                key = (
                    chain_index,
                    str(residue.seqid),
                    residue.name,
                    atom.name,
                )

                assert key not in atoms, f"Duplicated atom: {key}"
                assert atom.serial not in serial_to_key, (
                    f"Duplicated atom serial: {atom.serial}"
                )

                atoms[key] = (
                    atom.element.name,
                    atom.pos.x,
                    atom.pos.y,
                    atom.pos.z,
                )
                serial_to_key[atom.serial] = key
    return atoms, serial_to_key
