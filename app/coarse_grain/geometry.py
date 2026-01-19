from collections.abc import Iterable

from gemmi import Atom, Position


def calculate_center_of_mass(
    residue: Iterable[Atom], atom_names: list[str]
) -> Position | None:
    total_mass = 0.0
    x, y, z = 0.0, 0.0, 0.0

    for atom in residue:
        if atom.name in atom_names:
            mass = atom.element.weight
            x += atom.pos.x * mass
            y += atom.pos.y * mass
            z += atom.pos.z * mass
            total_mass += mass

    if total_mass == 0:
        return None

    return Position(x / total_mass, y / total_mass, z / total_mass)


def calculate_geometric_center(
    residue: Iterable[Atom], atom_names: list[str]
) -> Position | None:
    count = 0.0
    x, y, z = 0.0, 0.0, 0.0

    for atom in residue:
        if atom.name in atom_names:
            x += atom.pos.x
            y += atom.pos.y
            z += atom.pos.z
            count += 1.0

    if count == 0:
        return None

    return Position(x / count, y / count, z / count)
