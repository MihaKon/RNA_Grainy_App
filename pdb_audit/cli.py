import argparse
from pathlib import Path

from app.exceptions import FileProcessingError
from app.models.form import SupportedFormats
from pdb_audit import output
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
    arguments: argparse.Namespace, client: RcsbClient
) -> list[str]:
    pdb_ids: list[str] = []
    pdb_ids = client.get_all_rna_structure_ids()
    if arguments.all:
        return pdb_ids

    return pdb_ids[: int(arguments.number)]


def get_or_download_reference_structure(pdb_id: str, client: RcsbClient) -> Path:
    structure_directory = client.cache_directory / pdb_id
    structure_directory.mkdir(parents=True, exist_ok=True)
    file_path = structure_directory / f"{pdb_id}.cif"

    if file_path.exists():
        return file_path

    structure_content = client.download_structure(pdb_id)
    if not structure_content:
        raise FileProcessingError(f"Downloaded structure `{pdb_id}` is empty.")

    file_path.write_text(structure_content, encoding="utf-8")
    return file_path


def main() -> None:
    arguments = parse_arguments()
    pdb_ids: list[str] = []
    if arguments.ids:
        pdb_ids = get_structure_ids_from_cli(arguments)

    with RcsbClient() as client:
        cache_directory = client.cache_directory
        report_path = output.initialize_audit_report(cache_directory)
        if not pdb_ids:
            pdb_ids = get_structure_ids_from_pdb(arguments, client)

        for pdb_id in pdb_ids:
            try:
                file_path = get_or_download_reference_structure(pdb_id, client)

                validator = Validator.parse_files(
                    [file_path], SupportedFormats.CIF, None, [], []
                )
                validator.validate()

                for item in validator.validated_structures:
                    output.save_validated_structures(
                        item=item,
                        cache_directory=cache_directory,
                    )
                    output.append_structure_to_report(
                        item=item, report_path=report_path
                    )
            except Exception as error:
                print(f"Failed to process {pdb_id}: {error}")
                output.append_error_to_report(
                    pdb_id=pdb_id, error=error, report_path=report_path
                )

                continue


if __name__ == "__main__":
    main()
