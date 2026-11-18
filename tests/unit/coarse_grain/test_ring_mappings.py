import gemmi
import pytest

import app.coarse_grain.models as model_module
from app.coarse_grain.models import (
    BaseCoarseGrainModel,
    CalculateBeadModel,
    IFoldRNAModel,
    Nares2PModel,
    TopRNAModel,
)
from app.coarse_grain.residues import get_atoms

SUGAR_RING = ("C1'", "C2'", "C3'", "C4'", "O4'")
SIX_MEMBERED_BASE_RING = ("N1", "C2", "N3", "C4", "C5", "C6")
PURINE_RING_SYSTEM = SIX_MEMBERED_BASE_RING + ("N7", "C8", "N9")


def make_residue(name: str, index: int = 1) -> gemmi.Residue:
    residue = gemmi.Residue()
    residue.name = name
    residue.seqid = gemmi.SeqId(index, " ")
    residue.label_seq = index
    residue.entity_type = gemmi.EntityType.Polymer
    residue.het_flag = "A"
    for i, atom_name in enumerate(sorted(get_atoms(name))):
        atom = gemmi.Atom()
        atom.name = atom_name
        atom.element = gemmi.Element(atom_name[0])
        atom.pos = gemmi.Position(i % 5 + 5 * index, i % 3, i % 7)
        residue.add_atom(atom)
    return residue


def make_structure(*residues: gemmi.Residue) -> gemmi.Structure:
    structure = gemmi.Structure()
    model = gemmi.Model(1)
    chain = gemmi.Chain("A")
    for residue in residues:
        chain.add_residue(residue)
    model.add_chain(chain)
    structure.add_model(model)
    return structure


def reference_center(
    residue: gemmi.Residue, names: tuple[str, ...], *, mass_weighted: bool
) -> tuple[float, ...]:
    atoms = {atom.name: atom for atom in residue}
    selected = [atoms[name] for name in names]
    weights = [atom.element.weight if mass_weighted else 1.0 for atom in selected]
    return tuple(
        sum(getattr(atom.pos, axis) * w for atom, w in zip(selected, weights))
        / sum(weights)
        for axis in ("x", "y", "z")
    )


@pytest.mark.parametrize("residue_name", ["A", "G", "C", "U"])
@pytest.mark.parametrize("model_class", [TopRNAModel, IFoldRNAModel, Nares2PModel])
def test_bead_coordinates_use_published_ring_atoms(
    model_class: type[CalculateBeadModel], residue_name: str
) -> None:
    source = make_residue(residue_name)
    expected: dict[str, tuple[str, ...]] = {"S": SUGAR_RING}
    if model_class is TopRNAModel:
        expected = {
            "S": SUGAR_RING[:-1] + ("C5'", "O4'"),
            "B": PURINE_RING_SYSTEM
            if residue_name in ("A", "G")
            else SIX_MEMBERED_BASE_RING,
        }
    elif model_class is IFoldRNAModel:
        expected["B"] = SIX_MEMBERED_BASE_RING
    actual = source.clone()
    model_class()._get_residue_with_beads(actual)
    for bead_name, names in expected.items():
        bead = next(atom for atom in actual if atom.name == bead_name)
        assert (bead.pos.x, bead.pos.y, bead.pos.z) == pytest.approx(
            reference_center(source, names, mass_weighted=model_class is IFoldRNAModel)
        )


@pytest.mark.parametrize(
    ("model_class", "residue_name", "excluded"),
    [
        (TopRNAModel, "C", {"N4"}),
        (IFoldRNAModel, "A", {"C5'", "O2'", "O3'", "N7", "C8", "N9"}),
        (IFoldRNAModel, "U", {"O2"}),
        (Nares2PModel, "C", {"C5'", "O2'", "O3'", "O5'"}),
    ],
)
def test_atoms_outside_mapping_do_not_trigger_reconstruction(
    model_class: type[BaseCoarseGrainModel],
    residue_name: str,
    excluded: set[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_estimation(*args: object, **kwargs: object) -> None:
        pytest.fail("Atoms outside the published mapping must not be reconstructed.")

    monkeypatch.setattr(
        model_module, "estimate_missing_atom_positions", unexpected_estimation
    )
    residue = make_residue(residue_name)
    for i in range(len(residue) - 1, -1, -1):
        if residue[i].name in excluded:
            del residue[i]
    output = model_class().get_coarse_grain_structure(make_structure(residue))
    assert {atom.name for atom in output[0][0][0]} == {"P", "S", "B"}


def test_nares_phosphate_uses_midpoint_of_corrected_sugar_centers() -> None:
    first, second = make_residue("C", 1), make_residue("C", 2)
    centers = [
        reference_center(r, SUGAR_RING, mass_weighted=False) for r in (first, second)
    ]
    output = Nares2PModel().get_coarse_grain_structure(make_structure(first, second))
    bead = next(atom for atom in output[0][0][1] if atom.name == "P")
    assert (bead.pos.x, bead.pos.y, bead.pos.z) == pytest.approx(
        tuple((a + b) / 2 for a, b in zip(*centers))
    )
