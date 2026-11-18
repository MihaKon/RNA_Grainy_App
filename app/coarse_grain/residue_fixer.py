from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from math import isfinite

from gemmi import Atom, Element, Position, Residue, SupResult, cif, superpose_positions

from app.coarse_grain.residues import (
    BASE_ATOMS,
    SUGAR_RING_ATOMS,
    get_atoms,
    normalize_atom_name,
)
from app.settings import RESIDUE_TEMPLATES_DIR


@dataclass
class EstimationResult:
    positions: dict[str, Position]
    failures: dict[str, str]
    rmsd: float | None = None


@lru_cache(maxsize=4)
def load_template(residue_name: str) -> dict[str, Atom]:
    residue_atoms = get_atoms(residue_name)
    path = RESIDUE_TEMPLATES_DIR / f"{residue_name}.cif"

    block = cif.read_file(str(path)).sole_block()
    table = block.find(
        "_chem_comp_atom.",
        [
            "atom_id",
            "type_symbol",
            "pdbx_model_Cartn_x_ideal",
            "pdbx_model_Cartn_y_ideal",
            "pdbx_model_Cartn_z_ideal",
        ],
    )

    atoms = {}

    for row in table:
        atom_name = cif.as_string(row[0])

        if atom_name not in residue_atoms:
            continue

        atom = Atom()
        atom.name = atom_name
        atom.element = Element(cif.as_string(row[1]))
        atom.pos = Position(
            float(row[2]),
            float(row[3]),
            float(row[4]),
        )
        atoms[atom_name] = atom

    missing_atoms = residue_atoms - atoms.keys()

    if missing_atoms:
        raise ValueError(
            f"Incomplete template for {residue_name}: "
            f"{', '.join(sorted(missing_atoms))}"
        )

    return atoms


def _atoms_by_name(residue: Residue) -> dict[str, Atom]:
    atoms = {}

    for atom in residue:
        name = normalize_atom_name(atom.name)

        if name in atoms:
            raise ValueError(f"Duplicate atom after normalization: {name}")

        atoms[name] = atom

    return atoms


def _finite_position(position: Position) -> bool:
    return all(isfinite(value) for value in (position.x, position.y, position.z))


def select_reference_atoms(
    residue: Residue,
    template: Mapping[str, Atom],
) -> list[str]:
    present = _atoms_by_name(residue)

    return sorted(present.keys() & template.keys())


def _has_noncollinear_points(
    positions: Sequence[Position],
) -> bool:
    for a, b, c in combinations(positions, 3):
        u = b - a
        v = c - a

        if u.cross(v).length() > 0.05 * u.length() * v.length():
            return True

    return False


def check_reconstruction_support(
    residue: Residue,
    missing_atoms: set[str],
) -> str | None:
    present = {normalize_atom_name(atom.name): atom for atom in residue}

    fragments = (
        ("base", BASE_ATOMS[residue.name]),
        ("sugar ring", SUGAR_RING_ATOMS),
    )

    for fragment_name, fragment_atoms in fragments:
        if not missing_atoms & fragment_atoms:
            continue

        positions = [
            present[name].pos
            for name in sorted(fragment_atoms & present.keys())
            if _finite_position(present[name].pos)
        ]

        if len(positions) < 3 or not _has_noncollinear_points(positions):
            return (
                f"Insufficient reference atoms in the {fragment_name}: "
                "at least three noncollinear atoms are required."
            )

    return None


def fit_template(
    residue: Residue,
    template: Mapping[str, Atom],
    reference_atom_names: Sequence[str],
    max_rmsd: float | None = None,
) -> SupResult | None:
    names = list(dict.fromkeys(reference_atom_names))
    present = _atoms_by_name(residue)

    if len(names) < 3:
        return None

    if any(name not in present or name not in template for name in names):
        return None

    target = [present[name].pos for name in names]
    source = [template[name].pos for name in names]

    if not all(_finite_position(position) for position in target + source):
        return None

    if not _has_noncollinear_points(target):
        return None

    if not _has_noncollinear_points(source):
        return None

    fit = superpose_positions(target, source)

    if not isfinite(fit.rmsd):
        return None

    if max_rmsd is not None and fit.rmsd > max_rmsd:
        return None

    return fit


def estimate_missing_atom_positions(
    residue: Residue,
    missing_atoms: set[str],
    template: Mapping[str, Atom],
    max_rmsd: float | None = None,
) -> EstimationResult:
    missing = {normalize_atom_name(name) for name in missing_atoms}

    if not missing:
        return EstimationResult({}, {})

    reason = check_reconstruction_support(residue, missing)

    if reason is not None:
        return EstimationResult(
            positions={},
            failures={name: reason for name in sorted(missing)},
        )

    present = _atoms_by_name(residue)

    failures = {
        name: "Atom is absent from the template or already present."
        for name in missing
        if name not in template or name in present
    }

    references = select_reference_atoms(residue, template)

    fit = fit_template(
        residue,
        template,
        references,
        max_rmsd=max_rmsd,
    )

    if fit is None:
        return EstimationResult(
            positions={},
            failures={
                name: failures.get(
                    name,
                    "Insufficient reference geometry or rejected template fit.",
                )
                for name in missing
            },
        )

    positions = {}

    for name in sorted(missing - failures.keys()):
        point = fit.transform.apply(template[name].pos)
        position = Position(point.x, point.y, point.z)

        if not _finite_position(position):
            failures[name] = "Estimated coordinates are not finite."
        else:
            positions[name] = position

    return EstimationResult(
        positions=positions,
        failures=failures,
        rmsd=fit.rmsd,
    )


def validate_estimated_positions(
    residue: Residue,
    template: Mapping[str, Atom],
    positions: Mapping[str, Position],
) -> bool:
    present = _atoms_by_name(residue)

    return all(
        name in template and name not in present and _finite_position(position)
        for name, position in positions.items()
    )


def add_estimated_atoms(
    residue: Residue,
    template: Mapping[str, Atom],
    positions: Mapping[str, Position],
) -> None:
    if not validate_estimated_positions(
        residue,
        template,
        positions,
    ):
        raise ValueError("Cannot add invalid or already existing atoms.")

    for name, position in positions.items():
        atom = template[name].clone()
        atom.pos = position
        atom.altloc = "\0"
        atom.occ = 1.0
        atom.b_iso = 0.0

        residue.add_atom(atom)
