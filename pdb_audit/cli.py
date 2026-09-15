import argparse
from pathlib import Path

from app.models.form import SupportedFormats
from app.services.structures import StructureProcessor
from pdb_audit.client import RcsbClient
from pdb_audit.validators import ValidatedStructure, Validator


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
    arguments: argparse.Namespace, client: RcsbClient
) -> list[str]:
    pdb_ids: list[str] = []
    pdb_ids = client.get_all_rna_structure_ids()
    if arguments.all:
        return pdb_ids

    return pdb_ids[: int(arguments.number)]


def save_reference_structure(pdb_id: str, client: RcsbClient) -> Path:
    structure_directory = client.cache_directory / pdb_id
    structure_directory.mkdir(parents=True, exist_ok=True)
    file_path = structure_directory / f"{pdb_id}.cif"

    if not file_path.exists():
        structure_content = client.download_structure(pdb_id)
        if structure_content:
            file_path.write_text(structure_content, encoding="utf-8")
    return file_path


def save_coarse_grain_structures(
    item: ValidatedStructure, cache_directory: Path
) -> None:
    structure_directory = cache_directory / item.file_name
    structure_directory.mkdir(parents=True, exist_ok=True)

    for model_name, result in item.coarse_grain_results.items():
        file_path = structure_directory / f"{item.file_name}_{model_name}.cif"
        content = StructureProcessor.structure_to_cif_string(result.structure)
        file_path.write_text(content, encoding="utf-8")


def print_structure_report(item: ValidatedStructure) -> None:
    lines = [
        item.file_name,
        f"  reference: {item.reference_structure}",
    ]

    for model_name, result in item.coarse_grain_results.items():
        lines.append(f"  {model_name}: {result.structure}")

        for issue in result.issues:
            lines.append(f"    - {issue.code}: {issue.message}")

    lines.append("-" * 20)
    print("\n".join(lines))


def main() -> None:
    arguments = parse_arguments()
    pdb_ids: list[str] = []
    file_paths: list[Path] = []
    if arguments.ids:
        pdb_ids = get_structure_ids_from_cli(arguments)

    with RcsbClient() as client:
        if not pdb_ids:
            pdb_ids = get_structure_ids_from_pdb(arguments, client)

        for pdb_id in pdb_ids:
            file_path = save_reference_structure(pdb_id, client)
            file_paths.append(file_path)

    validator = Validator.parse_files(file_paths, SupportedFormats.CIF, None, [], [])
    validator.validate()
    for item in validator.structures:
        save_coarse_grain_structures(
            item,
            client.cache_directory,
        )
        print_structure_report(item)


if __name__ == "__main__":
    main()
