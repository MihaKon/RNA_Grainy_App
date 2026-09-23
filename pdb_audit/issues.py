from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum


class Severity(StrEnum):
    INFO = "INFO"  # Informational issues that do not affect the structure
    WARNING = "WARNING"  # Issues that affect the structure but are caused by algorithm limitations of parsing diversity of structures
    ERROR = "ERROR"  # Critical issues that prevent the structure from being used in simulations or analyses


class Issues(Enum):
    def __init__(self, code: str, message: str, severity: Severity):
        self.code = code
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        return f"{self.code}: {self.message} ({self.severity.value})"

    # GENERAL ISSUES #
    SOURCE_STRUCTURE_ALREADY_COARSE_GRAINED = (
        "source_structure_already_coarse_grained",
        "The downloaded structure appears to already use a reduced representation",
        Severity.INFO,
    )

    SOURCE_STRUCTURE_INCOMPATIBLE_WITH_COARSE_GRAIN_MODEL = (
        "source_structure_incompatible_with_coarse_grain_model",
        "The source structure does not contain enough atoms for the selected coarse-grained model",
        Severity.ERROR,
    )

    INVALID_NUMBER_OF_AA_ATOMS = (
        "invalid_number_of_aa_atoms",
        "The number of atoms in the parsed AA structure is not consistent with the number of atoms in the downloaded structure",
        Severity.ERROR,
    )

    INVALID_NUMBER_OF_AA_ATOMS_BY_ENTITY_TYPE = (
        "invalid_aa_atoms_by_entity_type",
        "Atom counts grouped by entity type do not match the downloaded CIF",
        Severity.ERROR,
    )

    INVALID_NUMBER_OF_BEADS = (
        "invalid_number_of_beads",
        "The generated bead multiset does not match the beads constructible from the source atoms",
        Severity.ERROR,
    )

    INVALID_NUMBER_OF_CONNECTIONS = (
        "invalid_number_of_connections",
        "The number of connections in the structure is invalid",
        Severity.ERROR,
    )

    INVALID_NUMBER_OF_CHAINS = (
        "invalid_number_of_chains",
        "The number of coarse-grained chains is not consistent wit the number of reference structure RNA chains",
        Severity.ERROR,
    )

    EMPTY_CHAIN = (
        "empty_chain",
        "There is empty chain in the coarse-grained structure",
        Severity.ERROR,
    )

    EMPTY_MODEL = (
        "empty_model",
        "There is empty model in the coarse-grained structure",
        Severity.ERROR,
    )

    # METADATA ISSUES #

    REFERENCE_CIF_ENTITY_METADATA_LOST = (
        "reference_cif_entity_metadata_lost",
        "Entity metadata was lost while serializing the reference structure",
        Severity.ERROR,
    )

    # NMR ISSUES #

    MERGED_NMR_MODELS = (
        "merged_nmr_models",
        "Multiple NMR models merged to one model in coarse structure",
        Severity.ERROR,
    )

    # Missing, wrong or incomplete residues in the structure #

    MISSING_MODIFIED_RESIDUE = (
        "missing_modified_residue",
        "A modified RNA residue is missing from the structure",
        Severity.WARNING,
    )

    BEAD_SKIPPED_DUE_TO_MISSING_SOURCE_ATOMS = (
        "bead_skipped_due_to_missing_source_atoms",
        "A bead was not generated because none of its configured source atoms were present",
        Severity.WARNING,
    )

    BEAD_GENERATED_FROM_INCOMPLETE_ATOM_SET = (
        "bead_generated_from_incomplete_atom_set",
        "A bead was generated from only part of its configured source atom set",
        Severity.WARNING,
    )

    WATER_IN_COARSE_STRUCTURE = (
        "water_in_coarse_structure",
        "A water residue is present in the coarse-grained structure",
        Severity.ERROR,
    )

    LIGAND_IN_COARSE_STRUCTURE = (
        "ligand_in_coarse_structure",
        "A ligand is present in the coarse-grained structure",
        Severity.ERROR,
    )

    NONPOLYMER_NUCLEOTIDE_IN_COARSE_STRUCTURE = (
        "nonpolymer_nucleotide_in_coarse_structure",
        "A non-polymer nucleotide is present in the coarse-grained structure",
        Severity.ERROR,
    )

    PROTEIN_RESIDUE_IN_COARSE_STRUCTURE = (
        "protein_residue_in_coarse_structure",
        "A protein residue is present in the coarse-grained structure",
        Severity.WARNING,
    )

    GAP_IN_COARSE_STRUCTURE = (
        "gap_in_coarse_structure",
        "There is a gap in the coarse-grained structure",
        Severity.WARNING,
    )

    DNA_RESIDUE_IN_COARSE_STRUCTURE = (
        "dna_residue_in_coarse_structure",
        "A DNA residue is present in the coarse-grained structure",
        Severity.WARNING,
    )

    ALTERNATIVE_ATOM_NAMES_NOT_SUPPORTED = (
        "alternative_atom_names_not_supported",
        "The reference structure contains alternative atom names that are not present in the coarse-grained structure",
        Severity.WARNING,
    )

    # CONNECTION ISSUES #

    CONNECTIVITY_NOT_FOUND = (
        "connectivity_not_found",
        "The connectivity of the coarse-grained structure could not be determined",
        Severity.ERROR,
    )

    CONNECTIVITY_BETWEEN_INVALID_BEADS = (
        "connectivity_between_invalid_beads",
        "The algorithm created connectivity between two beads that should not be connected, e.g because of lack of some bead",
        Severity.ERROR,
    )

    DUPLICATED_CONNECTIVITY = (
        "duplicated_connectivity",
        "The connectivity of the coarse-grained structure is duplicated",
        Severity.ERROR,
    )

    CONNECTIVITY_WITH_NOT_EXISTENT_BEAD = (
        "connectivity_with_not_existent_bead",
        "There is connectivity with bead thad does not exist in the coarse-grained structure",
        Severity.ERROR,
    )

    WRONG_CONNECTIVITY_TYPE = (
        "wrong_connectivity_type",
        "The connectivity of the coarse-grained structure is not 'covalent' as expected",
        Severity.WARNING,
    )

    # ALT LOCS ISSUES #

    ALT_LOC_PRESENT = (
        "alt_loc_present",
        "The structure contains alternative locations for some atoms",
        Severity.INFO,
    )

    ALT_LOC_B_OCCUPANCY_IS_HIGHER_THAN_A = (
        "alt_loc_b_occupancy_is_higher_than_a",
        "The algorithm chose A although B alt loc has higher occupancy",
        Severity.WARNING,
    )

    A_ALT_LOC_NOT_FOUND = (
        "a_alt_loc_not_found",
        "Structure contains different alt locs than A",
        Severity.WARNING,
    )

    # STRESS TESTS #


@dataclass
class IssueContent:
    code: str
    message: str | None = None
    severity: Severity | None = None
    model_index: int | None = None
    chain_name: str | None = None
    seq_id: int | None = None
    res_name: str | None = None

    @classmethod
    def from_issue(
        cls,
        issue: Issues,
        model_index: int | None = None,
        chain_name: str | None = None,
        seq_id: int | None = None,
        res_name: str | None = None,
    ) -> IssueContent:
        return cls(
            code=issue.code,
            message=issue.message,
            severity=issue.severity,
            model_index=model_index,
            chain_name=chain_name,
            seq_id=seq_id,
            res_name=res_name,
        )
