import type { CoarseGrainResult } from "@/api/types";

export interface ResultLocationState {
  result: CoarseGrainResult;
}

export function readResultState(
  state: unknown,
  workspaceId: string | undefined,
): CoarseGrainResult | null {
  if (typeof state !== "object" || state === null || !("result" in state)) {
    return null;
  }
  const { result } = state as ResultLocationState;
  return result.workspace_id === workspaceId ? result : null;
}
