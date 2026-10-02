from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class AppConfig(BaseModel):
    supported_file_formats: list[str]
    preset_ids: list[str]
    max_file_upload_size: int
    custom_model_json_max_chars: int
    custom_model_json_max_size: int


class Citation(BaseModel):
    number: int
    text: str
    url: str


class BeadMapping(BaseModel):
    bead_id: str
    bead: str
    description: str


class ResidueMapping(BaseModel):
    residue: str
    residue_type: str
    beads: list[BeadMapping]


class ModelDocumentation(BaseModel):
    id: str
    name: str
    description: str
    beads_per_residue: list[int]
    citations: list[Citation]
    mapping: list[ResidueMapping]
    image_url: str | None


class AtomCounts(BaseModel):
    original: int
    coarse: int
    reduction: float


class ResultFiles(BaseModel):
    reference_url: str
    coarse_mmcif_url: str
    coarse_pdb_url: str | None
    consumed_url: str


class CoarseGrainResult(BaseModel):
    workspace_id: str
    filename: str
    reference_format: str
    coarse_format: str
    files: ResultFiles
    atom_counts: AtomCounts
    selected_models: list[int]
    selected_chains: list[str]
    model: ModelDocumentation
