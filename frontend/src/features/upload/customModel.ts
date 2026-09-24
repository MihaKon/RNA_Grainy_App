import type { AppConfig } from "@/api/types";
import { formatBytes } from "@/lib/format";

export interface LoadedCustomModel {
  fileName: string;
  name: string;
  json: string;
}

export class CustomModelFileError extends Error {}

const DEFAULT_CUSTOM_MODEL_NAME = "Custom Model";

export async function readCustomModelFile(
  file: File,
  config: AppConfig,
): Promise<LoadedCustomModel> {
  if (file.size > config.custom_model_json_max_size) {
    throw new CustomModelFileError(
      `The file exceeds the ${formatBytes(config.custom_model_json_max_size)} limit.`,
    );
  }

  const json = await file.text();
  if (json.length > config.custom_model_json_max_chars) {
    throw new CustomModelFileError(
      `The model definition exceeds ${config.custom_model_json_max_chars.toString()} characters.`,
    );
  }

  let definition: unknown;
  try {
    definition = JSON.parse(json);
  } catch {
    throw new CustomModelFileError("The file is not valid JSON.");
  }

  if (
    typeof definition !== "object" ||
    definition === null ||
    Array.isArray(definition)
  ) {
    throw new CustomModelFileError("The model definition must be a JSON object.");
  }

  const name =
    "model_name" in definition &&
    typeof definition.model_name === "string" &&
    definition.model_name.trim()
      ? definition.model_name
      : DEFAULT_CUSTOM_MODEL_NAME;

  return { fileName: file.name, name, json };
}
