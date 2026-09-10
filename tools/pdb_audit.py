from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_FILE_URL = "https://files.rcsb.org/download/{pdb_id}.cif"

DEFAULT_DOWNLOAD_LIMIT_BYTES = 512 * 1024 * 1024
DEFAULT_PAGE_SIZE = 1_000


class IssueTypes(StrEnum):
    INFO = "info"  # Informational issues that do not affect the structure
    WARNING = "warning"  # Issues that affect the structure but are caused by algorithm limitations of parsing diversity of structures
    ERROR = "error"  # Critical issues that prevent the structure from being used in simulations or analyses


@dataclass
class IssueContent:
    code: str
    message: str
    model_index: int | None = None
    chain_name: str | None = None
    seq_id: int | None = None
    res_name: str | None = None


@dataclass
class Result:
    pdb_id: str
    issues: list[IssueContent] = field(default_factory=list)


class Issues(Enum):
    # RCSB ISSUES #

    # GENERAL ISSUES #
    INVALID_NUMBER_OF_AA_ATOMS = (
        "invalid_number_of_aa_atoms",
        "The number of atoms in the parsed AA structure is not consistent with the number of atoms in the downloaded structure",
        IssueTypes.ERROR,
    )

    INVALID_NUMBER_OF_BEADS = (
        "invalid_number_of_beads",
        "The number of beads in the structure is not consistent with the number of RNA residues",
        IssueTypes.ERROR,
    )

    INVALID_NUMBER_OF_CONNECTIONS = (
        "invalid_number_of_connections",
        "The number of connections in the structure is invalid",
        IssueTypes.ERROR,
    )

    INVALID_NUMBER_OF_CHAINS = (
        "invalid_number_of_chains",
        "The number of coarse-grained chains is not consistent wit the number of reference structure chains",
        IssueTypes.ERROR,
    )

    EMPTY_CHAIN = (
        "empty_chain",
        "There is empty chain in the coarse-grained structure",
        IssueTypes.ERROR,
    )

    EMPTY_MODEL = (
        "empty_model",
        "There is empty model in the coarse-grained structure",
        IssueTypes.ERROR,
    )

    # NMR ISSUES #

    MERGED_NMR_MODELS = (
        "merged_nmr_models",
        "Multiple NMR models merged to one model in coarse structure",
        IssueTypes.ERROR,
    )

    # Missing, wrong or incomplete residues in the structure #

    MISSING_MODIFIED_RESIDUE = (
        "missing_modified_residue",
        "A modified RNA residue is missing from the structure",
        IssueTypes.WARNING,
    )

    INCOMPLETE_RESIDUE_REMOVED = (
        "incomplete_residue_removed",
        "A bead has been removed from the structure because",
        IssueTypes.WARNING,
    )

    INCOMPLETE_RESIDUE_PRESENT = (
        "incomplete_residue_present",
        "A bead is present in the structure but it has been calculated from incomplete atom set",
        IssueTypes.WARNING,
    )

    IONS_OR_LIGANDS_IN_COARSE_STRUCTURE = (
        "ions_or_ligands_in_coarse_structure",
        "Ions, water or ligands are present in the coarse-grained structure",
        IssueTypes.WARNING,
    )

    PROTEIN_RESIDUE_IN_COARSE_STRUCTURE = (
        "protein_residue_in_coarse_structure",
        "A protein residue is present in the coarse-grained structure",
        IssueTypes.WARNING,
    )

    GAP_IN_COARSE_STRUCTURE = (
        "gap_in_coarse_structure",
        "There is a gap in the coarse-grained structure",
        IssueTypes.WARNING,
    )

    DNA_RESIDUE_IN_COARSE_STRUCTURE = (
        "dna_residue_in_coarse_structure",
        "A DNA residue is present in the coarse-grained structure",
        IssueTypes.WARNING,
    )

    ALTERNATIVE_ATOM_NAMES_NOT_SUPPORTED = (
        "alternative_atom_names_not_supported",
        "The reference structure contains alternative atom names that are not present in the coarse-grained structure",
        IssueTypes.WARNING,
    )

    # CONNECTION ISSUES #

    CONNECTIVITY_NOT_FOUND = (
        "connectivity_not_found",
        "The connectivity of the coarse-grained structure could not be determined",
        IssueTypes.ERROR,
    )

    CONNECTIVITY_BETWEEN_INVALID_BEADS = (
        "connectivity_between_invalid_beads",
        "The algorithm created connectivity between two beads that should not be connected, e.g because of lack of some bead",
        IssueTypes.ERROR,
    )

    DUPLICATED_CONNECTIVITY = (
        "duplicated_connectivity",
        "The connectivity of the coarse-grained structure is duplicated",
        IssueTypes.ERROR,
    )

    CONNECTIVITY_WITH_NOT_EXISTENT_BEAD = (
        "connectivity_with_not_existent_bead",
        "There is connectivity with bead thad does not exist in the coarse-grained structure",
        IssueTypes.ERROR,
    )

    WRONG_CONNECTIVITY_TYPE = (
        "wrong_connectivity_type",
        "The connectivity of the coarse-grained structure is not 'covalent' as expected",
        IssueTypes.WARNING,
    )

    # ALT LOCS ISSUES #

    ALT_LOC_PRESENT = (
        "alt_loc_present",
        "The structure contains alternative locations for some atoms",
        IssueTypes.INFO,
    )

    ALT_LOC_B_OCCUPANCY_IS_HIGHER_THAN_A = (
        "alt_loc_b_occupancy_is_higher_than_a",
        "The algorithm chose A although B alt loc has higher occupancy",
        IssueTypes.WARNING,
    )

    A_ALT_LOC_NOT_FOUND = (
        "a_alt_loc_not_found",
        "Structure contains different alt locs than A",
        IssueTypes.WARNING,
    )

    # STRESS TESTS #

    def __init__(self, code: str, message: str, issue_type: IssueTypes):
        self.code = code
        self.message = message
        self.issue_type = issue_type

    def __str__(self) -> str:
        return f"{self.code}: {self.message} ({self.issue_type.value})"
