from pathlib import Path

from gemmi import Structure

from app.services.structures import StructureProcessor
from pdb_audit.validators import ValidatedStructure


def save_structure_as_cif(structure: Structure, file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = StructureProcessor.structure_to_cif_string(structure)
    file_path.write_text(content, encoding="utf-8")


def save_validated_structures(item: ValidatedStructure, cache_directory: Path) -> None:
    structure_directory = cache_directory / item.file_name
    save_structure_as_cif(
        structure=item.reference_structure,
        file_path=structure_directory / f"{item.file_name}_reference.cif",
    )

    for model_name, result in item.coarse_grain_results.items():
        save_structure_as_cif(
            structure=result.structure,
            file_path=structure_directory / f"{item.file_name}_{model_name}.cif",
        )


def initialize_audit_report(cache_directory: Path) -> Path:
    report_path = cache_directory / "audit_report.txt"

    report_path.write_text(
        "RNAgrainy PDB audit report\n",
        encoding="utf-8",
    )

    return report_path


def format_structure_report(item: ValidatedStructure) -> str:
    lines = [
        item.file_name,
        f"  reference: {item.reference_structure}",
    ]

    for model_name, result in item.coarse_grain_results.items():
        lines.append(f"  {model_name}: {result.structure}")

        for issue in result.issues:
            lines.append(f"    - [{issue.severity}] {issue.code}: {issue.message}")

    lines.append("-" * 20)
    return "\n".join(lines)


def append_error_to_report(
    pdb_id: str,
    error: Exception,
    report_path: Path,
) -> None:
    content = f"FAILED: {pdb_id}\n  {type(error).__name__}: {error}\n{'=' * 20}\n\n"

    with report_path.open("a", encoding="utf-8") as report:
        report.write(content)


def append_structure_to_report(item: ValidatedStructure, report_path: Path) -> None:
    content = format_structure_report(item)
    print(content)
    with report_path.open("a", encoding="utf-8") as report:
        report.write(content)
        report.write("\n\n")
