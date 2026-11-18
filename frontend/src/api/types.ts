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
}

export interface CoarseGrainResult {
  workspace_id: string;
  filename: string;
  reference_format: "pdb" | "mmcif";
  coarse_format: "mmcif";
  files: ResultFiles;
  atom_counts: AtomCounts;
  selected_models: number[];
  selected_chains: string[];
  model: ModelDocumentation;
  report?: ConversionReport | null;
  custom_model?: Record<string, unknown> | null;
}

export interface ResidueConversion {
  model: number;
  chain: string;
  residue_id: string;
  residue_name: string;
  canonical_name: string;
  status: "converted" | "skipped";
  missing_atoms: string[];
  estimated_atoms: string[];
  created_beads: string[];
  skipped_beads: string[];
  failures: Record<string, string>;
  ignored_altlocs: string[];
  terminal_phosphate_absent: boolean;
}

export interface SkippedConnection {
  model: number;
  chain: string;
  source_residue: string;
  target_residue: string;
  source_bead: string;
  target_bead: string;
  distance: number;
}

export interface ConversionReport {
  created_beads: number;
  skipped_beads: number;
  skipped_residues: number;
  estimated_atoms: number;
  modified_residues: number;
  residues: ResidueConversion[];
  skipped_connections: SkippedConnection[];
}
