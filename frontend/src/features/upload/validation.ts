import { CUSTOM_MODEL_ID, type StructureSource } from "@/api/coarseGrain";
import type { AppConfig } from "@/api/types";
import { formatBytes, formatList } from "@/lib/format";

import type { LoadedCustomModel } from "./customModel";

export type SourceKind = StructureSource["kind"];

export interface UploadFormValues {
  sourceKind: SourceKind;
  file: File | null;
  rcsbId: string;
  presetId: string;
  modelId: string;
  customModel: LoadedCustomModel | null;
  models: string;
  chains: string;
}

export type UploadFormErrors = Partial<
  Record<"source" | "model" | "models" | "chains", string>
>;

const PDB_ID_PATTERN = /^[a-z0-9]{4}$/i;
const MODELS_PATTERN = /^[\d,\s]*$/;
const CHAINS_PATTERN = /^[a-z0-9,\s]*$/i;

export function validateUploadForm(
  values: UploadFormValues,
  config: AppConfig,
): UploadFormErrors {
  const errors: UploadFormErrors = {};

  const sourceError = validateSource(values, config);
  if (sourceError) errors.source = sourceError;

  if (!values.modelId) {
    errors.model = "Select a coarse-grained model.";
  } else if (values.modelId === CUSTOM_MODEL_ID && !values.customModel) {
    errors.model = "Load a custom model JSON file.";
  }

  if (!MODELS_PATTERN.test(values.models)) {
    errors.models = "Use model numbers separated by commas.";
  }
  if (!CHAINS_PATTERN.test(values.chains)) {
    errors.chains = "Use chain IDs (letters and digits) separated by commas.";
  }

  return errors;
}

export function hasErrors(errors: UploadFormErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function validateStructureFile(
  file: File,
  config: AppConfig,
): string | undefined {
  const extension = file.name.includes(".")
    ? (file.name.split(".").pop()?.toLowerCase() ?? "")
    : "";
  const formats = config.supported_file_formats;

  if (!formats.includes(extension)) {
    return `Unsupported file format. Use ${formatList(formats.map((f) => `.${f}`))}.`;
  }
  if (file.size === 0) {
    return "The file is empty.";
  }
  if (file.size > config.max_file_upload_size) {
    return `The file exceeds the ${formatBytes(config.max_file_upload_size)} limit.`;
  }
  return undefined;
}

export function toStructureSource(values: UploadFormValues): StructureSource | null {
  switch (values.sourceKind) {
    case "file":
      return values.file ? { kind: "file", file: values.file } : null;
    case "rcsb":
      return { kind: "rcsb", rcsbId: values.rcsbId.trim().toUpperCase() };
    case "preset":
      return { kind: "preset", presetId: values.presetId };
  }
}

function validateSource(
  values: UploadFormValues,
  config: AppConfig,
): string | undefined {
  switch (values.sourceKind) {
    case "file":
      return values.file
        ? validateStructureFile(values.file, config)
        : "Choose a structure file.";
    case "rcsb":
      return PDB_ID_PATTERN.test(values.rcsbId.trim())
        ? undefined
        : "Enter a 4-character PDB ID, e.g. 1EHZ.";
    case "preset":
      return values.presetId ? undefined : "Choose an example structure.";
  }
}
