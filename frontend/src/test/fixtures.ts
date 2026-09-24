import type { AppConfig, CoarseGrainResult, ModelDocumentation } from "@/api/types";

export const appConfig: AppConfig = {
  supported_file_formats: ["pdb", "cif", "mmcif"],
  preset_ids: ["1EHZ", "1MNX", "2F8S"],
  max_file_upload_size: 100 * 1024 ** 2,
  custom_model_json_max_chars: 5000,
  custom_model_json_max_size: 8 * 1024,
};

export const simRnaModel: ModelDocumentation = {
  id: "SimModel",
  name: "SimRNA",
  description: "The SimRNA [1] model.",
  beads_per_residue: [5],
  citations: [
    {
      number: 1,
      text: "Boniecki MJ et al.",
      url: "https://doi.org/10.1093/nar/gkv1479",
    },
  ],
  mapping: [
    {
      residue: "A",
      residue_type: "Purine",
      beads: [{ bead_id: "A1", bead: "P", description: "Phosphate P atom" }],
    },
  ],
  image_url: "/static/images/simmodel.png",
};

export const nastModel: ModelDocumentation = {
  ...simRnaModel,
  id: "NASTModel",
  name: "NAST",
  beads_per_residue: [1],
};

export const models = [nastModel, simRnaModel];

export const coarseGrainResult: CoarseGrainResult = {
  workspace_id: "4f1c2a9e-0000-4000-8000-000000000000",
  filename: "1EHZ",
  reference_format: "mmcif",
  coarse_format: "mmcif",
  files: {
    reference_url:
      "/api/results/4f1c2a9e-0000-4000-8000-000000000000/reference?file_format=mmcif",
    coarse_mmcif_url:
      "/api/results/4f1c2a9e-0000-4000-8000-000000000000/coarse?file_format=mmcif",
    coarse_pdb_url:
      "/api/results/4f1c2a9e-0000-4000-8000-000000000000/coarse?file_format=pdb",
    consumed_url: "/api/results/4f1c2a9e-0000-4000-8000-000000000000/consumed",
  },
  atom_counts: { original: 1821, coarse: 310, reduction: 0.8298 },
  selected_models: [],
  selected_chains: [],
  model: simRnaModel,
};
