from dataclasses import dataclass
from urllib.parse import urlencode

from fastapi import Request, UploadFile
from gemmi import Structure

from app.exceptions import FileProcessingError
from app.models.api import AtomCounts, CoarseGrainResult, ResultFiles
from app.models.form import COARSE_FILE_FORMAT, SupportedFormats
from app.rcsb import fetch_rcsb_file
from app.services.doc import DocsContextBuilder
from app.services.structures import StructureProcessor
from app.services.workspaces import WorkspaceManager
from app.settings import BYTES_PER_MIB, MAX_FILE_UPLOAD_SIZE, PRESETS_DIR

PDB_MAX_ATOM_COUNT = 99999


@dataclass(frozen=True)
class StructureSource:
    content: str
    filename: str
    file_format: SupportedFormats


@dataclass(frozen=True)
class CoarseGrainingOutcome:
    workspace_id: str
    original_atom_count: int
    coarse_atom_count: int

    @property
    def is_pdb_available(self) -> bool:
        return self.coarse_atom_count <= PDB_MAX_ATOM_COUNT

    @property
    def atom_reduction(self) -> float:
        if self.original_atom_count == 0:
            return 0.0
        return 1 - self.coarse_atom_count / self.original_atom_count


async def read_uploaded_structure(file: UploadFile) -> StructureSource:
    if file.size is None:
        raise FileProcessingError("Uploaded file is empty.")
    if file.size > MAX_FILE_UPLOAD_SIZE:
        max_size_mib = MAX_FILE_UPLOAD_SIZE / BYTES_PER_MIB
        raise FileProcessingError(
            f"File size exceeds maximum file upload size of: {max_size_mib:g} MiB."
        )

    try:
        content = (await file.read()).decode("utf-8")
    except UnicodeDecodeError as e:
        raise FileProcessingError(f"Error reading file: {e}")

    if content == "":
        raise FileProcessingError("Uploaded file is empty.")

    filename = file.filename or ""
    name, _, extension = filename.rpartition(".")
    return StructureSource(
        content=content,
        filename=name.split(".")[0],
        file_format=SupportedFormats(extension.lower()),
    )


async def fetch_rcsb_structure(rcsb_id: str) -> StructureSource:
    content = await fetch_rcsb_file(rcsb_id)
    if content is None:
        raise FileProcessingError(f"Could not fetch file for RCSB ID: {rcsb_id}")

    return StructureSource(
        content=content, filename=rcsb_id, file_format=SupportedFormats.CIF
    )


def read_preset_structure(preset_id: str) -> StructureSource:
    preset_path = PRESETS_DIR / f"{preset_id}.{SupportedFormats.CIF.value}"

    if not preset_path.exists():
        raise FileProcessingError(f"Preset file not found for ID: {preset_id}")

    try:
        content = preset_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise FileProcessingError(f"Error reading preset file: {e}")

    if content == "":
        raise FileProcessingError("Preset file is empty.")

    return StructureSource(
        content=content, filename=preset_id, file_format=SupportedFormats.CIF
    )


async def coarse_grain_structure(
    source: StructureSource,
    selected_model: str,
    models: list[int],
    chains: list[str],
    custom_model_data: dict | None = None,
) -> CoarseGrainingOutcome:
    original_structure = StructureProcessor.parse_structure(
        source.content, source.file_format, models=models, chains=chains
    )
    coarse_structure = StructureProcessor.apply_coarse_graining(
        original_structure, selected_model, custom_model_data
    )

    outcome = CoarseGrainingOutcome(
        workspace_id=WorkspaceManager.create_workspace_id(),
        original_atom_count=StructureProcessor.get_structure_atom_count(
            original_structure
        ),
        coarse_atom_count=StructureProcessor.get_structure_atom_count(coarse_structure),
    )
    await _save_structures(
        outcome, source.file_format, original_structure, coarse_structure
    )
    return outcome


async def _save_structures(
    outcome: CoarseGrainingOutcome,
    file_format: SupportedFormats,
    original_structure: Structure,
    coarse_structure: Structure,
) -> None:
    workspace_id = outcome.workspace_id
    original_format = file_format.normalize_format()

    original_content = StructureProcessor.structure_to_cif_string(original_structure)
    cif_content = StructureProcessor.structure_to_cif_string(coarse_structure)
    pdb_content = (
        StructureProcessor.structure_to_pdb_string(coarse_structure)
        if outcome.is_pdb_available
        else None
    )

    WorkspaceManager.setup_workspace_dir(workspace_id)

    try:
        if pdb_content is not None:
            await WorkspaceManager.create_file(
                workspace_id, pdb_content, f"coarse.{SupportedFormats.PDB.value}"
            )
        await WorkspaceManager.create_file(
            workspace_id, original_content, f"reference.{original_format.value}"
        )
        await WorkspaceManager.create_file(
            workspace_id, cif_content, f"coarse.{COARSE_FILE_FORMAT.value}"
        )
    except Exception:
        WorkspaceManager.cleanup_workspace(workspace_id)
        raise


def build_coarse_grain_result(
    request: Request,
    source: StructureSource,
    outcome: CoarseGrainingOutcome,
    selected_model: str,
    models: list[int],
    chains: list[str],
    custom_model_data: dict | None = None,
) -> CoarseGrainResult:
    reference_format = source.file_format.normalize_format()

    def result_file_url(file_type: str, file_format: SupportedFormats) -> str:
        path = request.app.url_path_for(
            "get_result_file", workspace_id=outcome.workspace_id, file_type=file_type
        )
        return f"{path}?{urlencode({'file_format': file_format.value})}"

    return CoarseGrainResult(
        workspace_id=outcome.workspace_id,
        filename=source.filename,
        reference_format=reference_format.value,
        coarse_format=COARSE_FILE_FORMAT.value,
        files=ResultFiles(
            reference_url=result_file_url("reference", reference_format),
            coarse_mmcif_url=result_file_url("coarse", COARSE_FILE_FORMAT),
            coarse_pdb_url=(
                result_file_url("coarse", SupportedFormats.PDB)
                if outcome.is_pdb_available
                else None
            ),
            consumed_url=str(
                request.app.url_path_for(
                    "mark_result_as_consumed", workspace_id=outcome.workspace_id
                )
            ),
        ),
        atom_counts=AtomCounts(
            original=outcome.original_atom_count,
            coarse=outcome.coarse_atom_count,
            reduction=outcome.atom_reduction,
        ),
        selected_models=models,
        selected_chains=chains,
        model=DocsContextBuilder.get_model_documentation(
            selected_model, custom_model_data
        ),
    )
