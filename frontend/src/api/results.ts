import { queryOptions } from "@tanstack/react-query";

import { apiFetch, apiRequest } from "./client";
import type { CoarseGrainResult, ResultFiles } from "./types";

export const resultQueryOptions = (workspaceId: string) =>
  queryOptions({
    queryKey: ["results", workspaceId, "metadata"],
    queryFn: ({ signal }) =>
      apiRequest<CoarseGrainResult>(`/api/results/${encodeURIComponent(workspaceId)}`, {
        signal,
      }),
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
  });

export interface ResultStructures {
  reference: string;
  coarseMmcif: string;
  coarsePdb: string | null;
  coarsePdbFailed: boolean;
}

async function fetchText(url: string): Promise<string> {
  return (await apiFetch(url)).text();
}

// The PDB file is optional, so a failed download must not hide the mmCIF result.
async function fetchOptionalText(url: string | null): Promise<string | null> {
  if (!url) {
    return null;
  }
  try {
    return await fetchText(url);
  } catch (error) {
    console.warn("Could not download the optional PDB file.", error);
    return null;
  }
}

export async function fetchResultStructures(
  files: ResultFiles,
): Promise<ResultStructures> {
  const [reference, coarseMmcif, coarsePdb] = await Promise.all([
    fetchText(files.reference_url),
    fetchText(files.coarse_mmcif_url),
    fetchOptionalText(files.coarse_pdb_url),
  ]);

  return {
    reference,
    coarseMmcif,
    coarsePdb,
    coarsePdbFailed: files.coarse_pdb_url !== null && coarsePdb === null,
  };
}

// Reuse the downloaded structure text for display controls and file downloads.
export const resultStructuresQueryOptions = (result: CoarseGrainResult) =>
  queryOptions({
    queryKey: ["results", result.workspace_id, "structures"],
    queryFn: () => fetchResultStructures(result.files),
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
  });
