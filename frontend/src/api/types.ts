// Mirrors the response models in app/models/api.py.

export interface AppConfig {
  supported_file_formats: string[];
  preset_ids: string[];
  max_file_upload_size: number;
  custom_model_json_max_chars: number;
  custom_model_json_max_size: number;
}

export interface Citation {
  number: number;
  text: string;
  url: string;
}

export interface BeadMapping {
  bead_id: string;
  bead: string;
  description: string;
}

export interface ResidueMapping {
  residue: string;
  residue_type: string;
  beads: BeadMapping[];
}

export interface ModelDocumentation {
  id: string;
  name: string;
  description: string;
  beads_per_residue: number[];
  citations: Citation[];
  mapping: ResidueMapping[];
  image_url: string | null;
}

export interface AtomCounts {
  original: number;
  coarse: number;
  reduction: number;
}

export interface ResultFiles {
  reference_url: string;
  coarse_mmcif_url: string;
  coarse_pdb_url: string | null;
  consumed_url: string;
}

export interface CoarseGrainResult {
  workspace_id: string;
  filename: string;
  reference_format: string;
  coarse_format: string;
  files: ResultFiles;
  atom_counts: AtomCounts;
  selected_models: number[];
  selected_chains: string[];
  model: ModelDocumentation;
}
