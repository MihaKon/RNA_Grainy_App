import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronDown } from "lucide-react";
import { lazy, type ReactNode, Suspense } from "react";
import { Link } from "react-router";

import { resultStructuresQueryOptions } from "@/api/results";
import type { CoarseGrainResult } from "@/api/types";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { AtomMappingTable } from "@/features/models/AtomMappingTable";
import { ModelDescription } from "@/features/models/ModelDescription";
import { downloadTextFile } from "@/lib/download";
import { formatBeadsPerResidue } from "@/lib/format";

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
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-label tracking-[0.15em] text-ink-3 uppercase">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-accent hover:text-accent-hover"
        >
          <ArrowLeft aria-hidden="true" className="size-3" /> New structure
        </Link>
        <span aria-hidden="true">/</span>
        <span>Job {result.workspace_id.slice(0, 8)}</span>
        <span className="inline-flex items-center gap-1.5">
          <span aria-hidden="true" className="size-1.5 rounded-full bg-blue" />
          Completed
        </span>
      </div>

      <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-hero-compact text-ink lg:text-heading">
            Coarse-grained <span className="text-accent">{result.filename}</span>
          </h1>
          <p className="text-sm text-ink-2">
            {model.name} — {formatBeadsPerResidue(model.beads_per_residue)}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
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
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[3fr_2fr]">
        <div>
          {structuresQuery.isError ? (
            <Alert severity="error">
              <p className="font-medium">The result could not be loaded.</p>
              <p className="text-ink-2">
                It may have expired. Please{" "}
                <Link to="/" className="text-accent hover:text-accent-hover">
                  process the structure again
                </Link>
                .
              </p>
            </Alert>
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

        <div className="flex flex-col gap-4">
          <ModelReport result={result} />

          <Alert severity="info">
            <ul className="flex list-disc flex-col gap-1 pl-4">
              <li>
                Reference atoms are counted from the first model and all chains unless a
                selection was made.
              </li>
              {pdbAvailable ? (
                <li>
                  Chain names may be shortened in PDB files of large structures. Check
                  the output before further use.
                </li>
              ) : (
                <li>
                  PDB output is unavailable for structures with 100,000 or more atoms.
                </li>
              )}
            </ul>
          </Alert>

          <Disclosure title="Model description">
            <ModelDescription model={model} />
          </Disclosure>
          <Disclosure title="Atom mapping">
            <AtomMappingTable mapping={model.mapping} />
          </Disclosure>
        </div>
      </div>
    </div>
  );
}

function ViewerPlaceholder() {
  return (
    <div
      role="status"
      className="flex h-[55dvh] min-h-80 items-center justify-center rounded-md bg-blue-ink font-mono text-label tracking-[0.15em] text-white/70 uppercase"
    >
      Loading structures…
    </div>
  );
}

function Disclosure({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="group rounded-md border border-line-soft bg-white">
      <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 [&::-webkit-details-marker]:hidden">
        <span className="eyebrow">{title}</span>
        <ChevronDown
          aria-hidden="true"
          className="size-4 text-ink-3 transition-transform group-open:rotate-180"
        />
      </summary>
      <div className="border-t border-dashed border-line-soft px-5 py-4">
        {children}
      </div>
    </details>
  );
}
