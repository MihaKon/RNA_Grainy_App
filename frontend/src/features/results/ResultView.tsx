import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { lazy, Suspense } from "react";
import { Link } from "react-router";

import { ApiError, getErrorMessage } from "@/api/client";
import { resultStructuresQueryOptions } from "@/api/results";
import type { CoarseGrainResult } from "@/api/types";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Disclosure } from "@/components/ui/Disclosure";
import { AtomMappingTable } from "@/features/models/AtomMappingTable";
import { ModelDescription } from "@/features/models/ModelDescription";
import { downloadTextFile } from "@/lib/download";

import { ModelReport } from "./ModelReport";
import { preloadStructureViewer } from "./viewer/preload";

const StructureViewer = lazy(() =>
  preloadStructureViewer().then((module) => ({ default: module.StructureViewer })),
);

export function ResultView({ result }: { result: CoarseGrainResult }) {
  const structuresQuery = useQuery(resultStructuresQueryOptions(result));
  const structures = structuresQuery.data;
  const { model } = result;
  const downloadName = `${result.filename}_${model.name}`;
  const pdbAvailable = result.files.coarse_pdb_url !== null;

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 lg:px-8">
      <Link
        to="/"
        className="inline-flex items-center gap-1 font-mono text-label tracking-[0.15em] text-accent uppercase hover:text-accent-hover"
      >
        <ArrowLeft aria-hidden="true" className="size-3" /> New structure
      </Link>

      <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
        <h1 className="font-display text-hero-compact text-ink lg:text-heading">
          {result.filename}
        </h1>
        <div className="flex flex-wrap gap-3">
          <Button
            variant={pdbAvailable ? "ghost" : "primary"}
            disabled={!structures}
            onClick={() => {
              if (structures) {
                downloadTextFile(structures.coarseMmcif, `${downloadName}.cif`);
              }
            }}
          >
            Download mmCIF
          </Button>
          {pdbAvailable && (
            <Button
              disabled={!structures?.coarsePdb}
              onClick={() => {
                if (structures?.coarsePdb) {
                  downloadTextFile(structures.coarsePdb, `${downloadName}.pdb`);
                }
              }}
            >
              Download PDB
            </Button>
          )}
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[3fr_2fr]">
        <div className="min-w-0">
          {structuresQuery.isError ? (
            <ResultLoadError error={structuresQuery.error} />
          ) : (
            <Suspense fallback={<ViewerPlaceholder />}>
              {structures ? (
                <StructureViewer
                  structures={structures}
                  referenceFormat={result.reference_format}
                />
              ) : (
                <ViewerPlaceholder />
              )}
            </Suspense>
          )}
        </div>

        <div className="flex min-w-0 flex-col gap-4">
          <ModelReport result={result} />
          <Disclosure title="Model description">
            <ModelDescription model={model} />
          </Disclosure>
          <Disclosure title="Atom mapping">
            <AtomMappingTable mapping={model.mapping} />
          </Disclosure>
          <Alert severity="info">
            <ul className="flex list-disc flex-col gap-1 pl-4">
              <li>
                Input atoms are the polymer atoms of the first model across all chains,
                unless specific models or chains were selected. Water, ions and ligands
                are not counted.
              </li>
              <li>
                {structures?.coarsePdbFailed
                  ? "The PDB file could not be downloaded. The mmCIF file is still available."
                  : pdbAvailable
                    ? "Chain names in PDB files of large structures may be shortened, so check the file before further use."
                    : "PDB output is unavailable for structures with 100,000 or more atoms; use mmCIF instead."}
              </li>
              <li>
                Some beads may be skipped for incomplete residues or residues with
                incorrect atoms, because the atoms they are built from are missing or
                wrong.
              </li>
            </ul>
          </Alert>
        </div>
      </div>
    </div>
  );
}

function ResultLoadError({ error }: { error: Error }) {
  const expired = error instanceof ApiError && error.status === 404;

  return (
    <Alert severity="error">
      <p className="font-medium">
        {expired ? "This result has expired." : "The result could not be loaded."}
      </p>
      <p className="text-ink-2">
        {expired
          ? "Result files are kept for about an hour after they are first opened. "
          : `${getErrorMessage(error)} `}
        Please{" "}
        <Link to="/" className="text-accent hover:text-accent-hover">
          process the structure again
        </Link>
        .
      </p>
    </Alert>
  );
}

function ViewerPlaceholder() {
  return (
    <div
      role="status"
      className="flex h-[55dvh] min-h-80 items-center justify-center rounded-md border border-line-soft bg-white font-mono text-label tracking-[0.15em] text-ink-3 uppercase"
    >
      Loading structures…
    </div>
  );
}
