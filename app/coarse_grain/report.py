from typing import Literal

from gemmi import Residue, Structure
from pydantic import BaseModel, Field


class ResidueConversion(BaseModel):
    model: int
    chain: str
    residue_id: str
    residue_name: str
    canonical_name: str
    status: Literal["converted", "skipped"] = "converted"
    missing_atoms: list[str] = Field(default_factory=list)
    estimated_atoms: list[str] = Field(default_factory=list)
    created_beads: list[str] = Field(default_factory=list)
    skipped_beads: list[str] = Field(default_factory=list)
    failures: dict[str, str] = Field(default_factory=dict)
    ignored_altlocs: list[str] = Field(default_factory=list)
    terminal_phosphate_absent: bool = False


class SkippedConnection(BaseModel):
    model: int
    chain: str
    source_residue: str
    target_residue: str
    source_bead: str
    target_bead: str
    distance: float


class ConversionReport(BaseModel):
    created_beads: int = 0
    skipped_beads: int = 0
    skipped_residues: int = 0
    estimated_atoms: int = 0
    modified_residues: int = 0
    residues: list[ResidueConversion] = Field(default_factory=list)
    skipped_connections: list[SkippedConnection] = Field(default_factory=list)


class ConversionReportCollector:
    def __init__(self, original: Structure) -> None:
        self.report = ConversionReport()
        self.original_names = {
            (model.num, chain.name, str(residue.seqid), residue.segment): residue.name
            for model in original
            for chain in model
            for residue in chain
        }

    def start(self, model: int, chain: str, residue: Residue) -> ResidueConversion:
        return ResidueConversion(
            model=model,
            chain=chain,
            residue_id=str(residue.seqid),
            residue_name=self.original_names[
                (model, chain, str(residue.seqid), residue.segment)
            ],
            canonical_name=residue.name,
            ignored_altlocs=sorted(
                {atom.altloc for atom in residue if atom.altloc not in ("\0", "A")}
            ),
        )

    def finish(
        self,
        entry: ResidueConversion,
        residue: Residue,
        expected_beads: list[str],
        *,
        skipped: bool = False,
    ) -> None:
        entry.status = "skipped" if skipped else "converted"
        entry.created_beads = [] if skipped else [atom.name for atom in residue]
        entry.skipped_beads = sorted(set(expected_beads) - set(entry.created_beads))
        report = self.report
        report.created_beads += len(entry.created_beads)
        report.skipped_beads += len(entry.skipped_beads)
        report.skipped_residues += int(skipped)
        report.estimated_atoms += len(entry.estimated_atoms)
        modified = entry.residue_name != entry.canonical_name
        report.modified_residues += int(modified)
        if (
            modified
            or entry.missing_atoms
            or entry.skipped_beads
            or entry.ignored_altlocs
            or skipped
        ):
            report.residues.append(entry)

    def record_skipped_connection(
        self,
        model: int,
        chain: str,
        previous: Residue,
        current: Residue,
        tail: str,
        head: str,
        distance: float,
    ) -> None:
        self.report.skipped_connections.append(
            SkippedConnection(
                model=model,
                chain=chain,
                source_residue=str(previous.seqid),
                target_residue=str(current.seqid),
                source_bead=tail,
                target_bead=head,
                distance=distance,
            )
        )
