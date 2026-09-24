import { queryOptions } from "@tanstack/react-query";

import { apiFetch } from "./client";
import type { CoarseGrainResult, ResultFiles } from "./types";

export interface ResultStructures {
  reference: string;
  coarseMmcif: string;
  coarsePdb: string | null;
}

async function fetchText(url: string): Promise<string> {
  return (await apiFetch(url)).text();
}

export async function fetchResultStructures(
  files: ResultFiles,
): Promise<ResultStructures> {
  const [reference, coarseMmcif, coarsePdb] = await Promise.all([
    fetchText(files.reference_url),
    fetchText(files.coarse_mmcif_url),
    files.coarse_pdb_url ? fetchText(files.coarse_pdb_url) : null,
  ]);

  try {
    await apiFetch(files.consumed_url, { method: "POST" });
  } catch (error) {
    // The cleanup worker removes unconsumed workspaces, so the result stays usable.
    console.warn("Could not mark the result as consumed.", error);
  }

  return { reference, coarseMmcif, coarsePdb };
}

// The workspace is deleted once consumed, so the files can be fetched exactly once.
export const resultStructuresQueryOptions = (result: CoarseGrainResult) =>
  queryOptions({
    queryKey: ["results", result.workspace_id, "structures"],
    queryFn: () => fetchResultStructures(result.files),
    staleTime: Infinity,
    retry: false,
  });
