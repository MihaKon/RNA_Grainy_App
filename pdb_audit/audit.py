import argparse

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_FILE_URL = "https://files.rcsb.org/download/{pdb_id}.cif"

DEFAULT_DOWNLOAD_LIMIT_BYTES = 512 * 1024 * 1024
DEFAULT_PAGE_SIZE = 1_000


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser_group = parser.add_mutually_exclusive_group(required=True)

    parser_group.add_argument(
        "--ids",
        nargs="+",
        metavar="PDB_ID",
        help="Download selected PDB structures.",
    )

    parser_group.add_argument(
        "--all", action="store_true", help="Download all PDB entries containing RNA."
    )

    parser_group.add_argument(
        "--number",
        metavar="N",
        help="Download N PDB entries containing RNA.",
    )

    return parser.parse_args()
