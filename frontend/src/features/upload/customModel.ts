import type { AppConfig } from "@/api/types";
import { formatBytes } from "@/lib/format";

export interface LoadedCustomModel {
  origin: string;
  name: string;
  json: string;
}

export class CustomModelFileError extends Error {}

const DEFAULT_CUSTOM_MODEL_NAME = "Custom Model";

// Mirrors the limits checked in app/models/form.py.
export function customModelSizeIssues(json: string, config: AppConfig): string[] {
  const issues: string[] = [];
  if (new TextEncoder().encode(json).byteLength > config.custom_model_json_max_size) {
    issues.push(
      `The model definition exceeds the ${formatBytes(config.custom_model_json_max_size)} limit.`,
    );
  }
  if (json.length > config.custom_model_json_max_chars) {
    issues.push(
      `The model definition exceeds ${config.custom_model_json_max_chars.toString()} characters.`,
    );
  }
  return issues;
}

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
  const [sizeIssue] = customModelSizeIssues(json, config);
  if (sizeIssue) throw new CustomModelFileError(sizeIssue);

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

  return { origin: file.name, name, json };
}
