import { apiRequest } from "./client";
import type { CoarseGrainResult } from "./types";

export type StructureSource =
  | { kind: "file"; file: File }
  | { kind: "rcsb"; rcsbId: string }
  | { kind: "preset"; presetId: string };

export interface CoarseGrainRequest {
  source: StructureSource;
  modelId: string;
  customModelJson?: string;
  models?: string;
  chains?: string;
}

export const CUSTOM_MODEL_ID = "custom";

export function coarseGrain(request: CoarseGrainRequest): Promise<CoarseGrainResult> {
  const body = new FormData();
  body.append("selected_model", request.modelId);
  appendIfPresent(body, "custom_model_data", request.customModelJson);
  appendIfPresent(body, "models", request.models);
  appendIfPresent(body, "chains", request.chains);

  const { source } = request;
  switch (source.kind) {
    case "file":
      body.append("file", source.file);
      break;
    case "rcsb":
      body.append("rcsb_id", source.rcsbId);
      break;
    case "preset":
      body.append("preset_id", source.presetId);
      break;
  }

  return apiRequest<CoarseGrainResult>(`/api/coarse-grain/${source.kind}`, {
    method: "POST",
    body,
  });
}

function appendIfPresent(body: FormData, name: string, value: string | undefined) {
  const trimmed = value?.trim();
  if (trimmed) {
    body.append(name, trimmed);
  }
}
