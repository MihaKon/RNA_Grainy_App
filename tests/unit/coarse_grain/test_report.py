from pathlib import Path

import gemmi
import pytest

from app.coarse_grain.models import (
    BaseCoarseGrainModel,
    IFoldRNAModel,
    Nares2PModel,
    SimModel,
)
from app.coarse_grain.report import ConversionReportCollector
from app.coarse_grain.residues import BASE_ATOMS


def source_structure(test_data_dir: Path) -> gemmi.Structure:
    return gemmi.read_structure(str(test_data_dir / "1EHZ.cif"))


@pytest.mark.parametrize("model_class", [SimModel, IFoldRNAModel, Nares2PModel])
def test_reporting_preserves_output_and_counts_all_models(
    test_data_dir: Path, model_class: type[BaseCoarseGrainModel]
) -> None:
    source = source_structure(test_data_dir)
    second = source[0].clone()
    second.num = 7
    source.add_model(second)
    before = source.make_mmcif_document().as_string()
    model = model_class()
    expected = model.get_coarse_grain_structure(source)
    collector = ConversionReportCollector(source)
    actual = model.get_coarse_grain_structure(source, collector)
    assert (
        actual.make_mmcif_document().as_string()
        == expected.make_mmcif_document().as_string()
    )
    assert collector.report.created_beads == sum(m.count_atom_sites() for m in actual)
    assert {entry.model for entry in collector.report.residues} == {1, 7}
    assert source.make_mmcif_document().as_string() == before


@pytest.mark.parametrize("remove_base", [False, True])
def test_report_records_actual_estimation_or_whole_residue_skip(
    test_data_dir: Path, remove_base: bool
) -> None:
    source = source_structure(test_data_dir)
    residue = next(r for r in source[0][0] if r.name == "A")
    seqid = str(residue.seqid)
    missing = BASE_ATOMS["A"] if remove_base else {"C4'"}
    for index in range(len(residue) - 1, -1, -1):
        if residue[index].name in missing:
            del residue[index]
    collector = ConversionReportCollector(source)
    SimModel().get_coarse_grain_structure(source, collector)
    entry = next(e for e in collector.report.residues if e.residue_id == seqid)
    if remove_base:
        assert entry.status == "skipped"
        assert entry.failures
        assert entry.skipped_beads
        assert not entry.created_beads
        assert not entry.estimated_atoms
        assert collector.report.skipped_residues == 1
    else:
        assert entry.status == "converted"
        assert entry.missing_atoms == ["C4'"]
        assert entry.estimated_atoms == ["C4'"]
        assert "C4'" in entry.created_beads
        assert not entry.failures


def test_terminal_phosphate_is_reported_without_repair(test_data_dir: Path) -> None:
    source = source_structure(test_data_dir)
    residue = source[0][0][0]
    for index in range(len(residue) - 1, -1, -1):
        if residue[index].name in {"P", "OP1", "OP2"}:
            del residue[index]
    collector = ConversionReportCollector(source)
    SimModel().get_coarse_grain_structure(source, collector)
    entry = next(e for e in collector.report.residues if e.residue_id == "1")
    assert entry.terminal_phosphate_absent
    assert entry.status == "converted"
    assert "P" in entry.skipped_beads
    assert not entry.estimated_atoms


@pytest.mark.parametrize("model_class", [SimModel, Nares2PModel])
def test_overlong_connections_are_reported(
    test_data_dir: Path, model_class: type[BaseCoarseGrainModel]
) -> None:
    source = source_structure(test_data_dir)
    residue = source[0][0][9]
    for atom in residue:
        atom.pos = atom.pos + gemmi.Position(50, 0, 0)
    collector = ConversionReportCollector(source)
    model_class().get_coarse_grain_structure(source, collector)
    omitted = collector.report.skipped_connections
    assert any(e.source_residue == "10" or e.target_residue == "10" for e in omitted)
    assert all(e.distance > 8 for e in omitted)
