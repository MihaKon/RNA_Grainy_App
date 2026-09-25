from pathlib import Path

from app.coarse_grain.models import CoarseGrainModelRegistry
from app.services.structures import StructureProcessor
from pdb_audit.issues import IssueContent
from pdb_audit.validators import ValidatedStructure


def save_structure_as_cif(content: str, file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def save_issue_artifacts(item: ValidatedStructure, cache_directory: Path) -> None:
    if not item.has_issues:
        return

    structure_directory = cache_directory / item.file_name

    reference_content = StructureProcessor.reference_structure_to_cif_string(
        structure=item.reference_structure,
        source_content=item.original_reference_cif,
        filename=item.file_name,
    )
    save_structure_as_cif(
        content=reference_content,
        file_path=structure_directory / f"{item.file_name}_reference.cif",
    )

    for model_name, result in item.coarse_grain_results.items():
        if not result.issues:
            continue
        coarse_content = StructureProcessor.coarse_structure_to_cif_string(
            structure=result.structure,
            model_name=CoarseGrainModelRegistry.get_model(model_name).name_verbose,
            filename=item.file_name,
        )
        save_structure_as_cif(
            content=coarse_content,
            file_path=structure_directory / f"{item.file_name}_{model_name}.cif",
        )


def initialize_audit_report(cache_directory: Path) -> Path:
    report_path = cache_directory / "audit_report.txt"

    report_path.write_text(
        "RNAgrainy PDB audit report\n",
        encoding="utf-8",
    )

    return report_path


def format_issue_location(issue: IssueContent) -> str:
    parts: list[str] = []

    if issue.model_index is not None:
        parts.append(f"model={issue.model_index}")

    if issue.chain_name is not None:
        parts.append(f"chain={issue.chain_name}")

    if issue.seq_id is not None:
        parts.append(f"residue={issue.seq_id}")

    if issue.res_name is not None:
        parts.append(f"res_name={issue.res_name}")

    if not parts:
        return ""

    return f" ({', '.join(parts)})"


def format_structure_report(item: ValidatedStructure) -> str:
    if item.has_issues:
        lines = [
            f"{item.file_name} ISSUES",
            f"  reference: {item.reference_structure}",
        ]

        for issue in item.reference_issues:
            location = format_issue_location(issue)
            lines.append(
                f"    - [{issue.severity}] {issue.code}{location}: {issue.message}"
            )
        for model_name, result in item.coarse_grain_results.items():
            if result.issues:
                lines.append(f"  {model_name}: {result.structure}")

                for issue in result.issues:
                    location = format_issue_location(issue)
                    lines.append(
                        f"    - [{issue.severity}] {issue.code}{location}: {issue.message}"
                    )

        lines.append("-" * 20)
    else:
        lines = [
            f"{item.file_name} PASSED",
        ]

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
        report.write("\n")
