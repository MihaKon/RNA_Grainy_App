import argparse
from pathlib import Path

from app.models.form import SupportedFormats
from pdb_audit.client import RcsbClient
from pdb_audit.validators import Validator


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


def get_structure_ids_from_cli(arguments: argparse.Namespace) -> list[str]:
    return [pdb_id.strip().upper() for pdb_id in arguments.ids]


def get_structure_ids_from_pdb(
    arguments: argparse.Namespace, client: RcsbClient | None = None
) -> list[str]:
    pdb_ids: list[str] = []
    if client:
        pdb_ids = client.get_all_rna_structure_ids()
        if arguments.all:
            return pdb_ids

    return pdb_ids[: int(arguments.number)]


def read(cache_directory: Path, pdb_ids: list[str]) -> None:
    file_paths: list[Path] = []
    for pdb_id in pdb_ids:
        file_paths.append(cache_directory / f"{pdb_id}.cif")
    validator = Validator.parse_files(file_paths, SupportedFormats.CIF, None, [], [])
    for item in validator.structures:
        print(f"{item.file_name}")
        print(f"  reference: {item.reference_structure}")

        for model_name, cg_structure in item.coarse_grain_structures.items():
            print(f"  {model_name}: {cg_structure}")
        print("-" * 20)


def main() -> None:
    arguments = parse_arguments()
    pdb_ids = []
    if arguments.ids:
        pdb_ids = get_structure_ids_from_cli(arguments)

    with RcsbClient() as client:
        if not pdb_ids:
            pdb_ids = get_structure_ids_from_pdb(arguments, client)
        cache_dir = Path(client.cache_directory)

        for pdb_id in pdb_ids:
            file_path = cache_dir / f"{pdb_id}.cif"
            if not file_path.exists():
                structure_content = client.download_structure(pdb_id)
                if structure_content:
                    file_path.write_text(structure_content, encoding="utf-8")
        read(cache_dir, pdb_ids)


if __name__ == "__main__":
    main()
