import argparse
from pathlib import Path

from pdb_audit.client import RcsbClient


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


def select_structure_ids(
    arguments: argparse.Namespace,
    client: RcsbClient,
) -> list[str]:
    if arguments.ids is not None:
        return [pdb_id.strip().upper() for pdb_id in arguments.ids]

    pdb_ids = client.get_all_rna_structure_ids()
    if arguments.all:
        return pdb_ids

    return pdb_ids[: int(arguments.number)]


def main() -> None:
    arguments = parse_arguments()
    with RcsbClient() as client:
        pdb_ids = select_structure_ids(arguments, client)
        for pdb_id in pdb_ids:
            structure_content = client.download_structure(pdb_id)
            if structure_content:
                file_path = Path(client.cache_directory) / f"{pdb_id}.cif"
                if not file_path.exists():
                    file_path.write_text(structure_content, encoding="utf-8")


if __name__ == "__main__":
    main()
