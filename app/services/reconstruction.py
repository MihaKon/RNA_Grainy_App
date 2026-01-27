import subprocess
from pathlib import Path
from app.exceptions import ReconstructionError
from app.formats import SupportedFormats
from app.services.jobs import JobManager
from app.services.structures import StructureProcessor
from app.settings import ARENA_DIR

ARENA_DEFAULT_PARAMETER = "5"

# TODO: Initial version of this functionality.


def to_wsl_path(win_path: Path) -> str:
    pure_path = win_path.resolve()
    drive = pure_path.drive.replace(":", "").lower()
    parts = list(pure_path.parts[1:])
    return f"/mnt/{drive}/" + "/".join(parts)


async def add_metadata_to_reconstructed_structure(
    job_id: str, selected_model: str, filename: str
) -> None:
    file_path = JobManager.get_file_path(job_id, "coarse_reconstructed.pdb")
    structure = StructureProcessor.read_structure_from_file(
        file_path.read_text(encoding="utf-8"), SupportedFormats.PDB
    )

    structure.name = f"Reconstructed structure {selected_model} for {filename}"
    structure.info["_entry.id"] = f"{filename[:4]}"
    structure.info["_struct.title"] = structure.name

    pdb_content = StructureProcessor.structure_to_pdb_string(structure)
    await JobManager.create_file(job_id, pdb_content, "coarse_reconstructed.pdb")


async def reconstruct_structure_using_arena(
    job_id: str, selected_model: str, filename: str
) -> None:
    win_input_path: Path = JobManager.get_file_path(job_id, "coarse.pdb")
    win_output_path: Path = JobManager.reconstruct_file_path(
        job_id, "coarse_reconstructed.pdb"
    )

    wsl_arena_bin = to_wsl_path(ARENA_DIR)
    wsl_input = to_wsl_path(win_input_path)
    wsl_output = to_wsl_path(win_output_path)

    command = ["wsl", wsl_arena_bin, wsl_input, wsl_output, ARENA_DEFAULT_PARAMETER]

    try:
        subprocess.run(command, capture_output=True, text=True, check=True)

        await add_metadata_to_reconstructed_structure(job_id, selected_model, filename)
    except subprocess.CalledProcessError as e:
        raise ReconstructionError(
            f"Arena reconstruction failed: {e.stderr or e.stdout}. Check your coarse grain model definition."
        ) from e
