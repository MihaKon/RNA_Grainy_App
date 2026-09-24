import { ArrowLeft } from "lucide-react";
import { Link, useLocation, useParams } from "react-router";

import type { CoarseGrainResult } from "@/api/types";
import { PageHero } from "@/components/layout/PageHero";
import { buttonClasses } from "@/components/ui/buttonStyles";
import { formatBeadsPerResidue, formatPercent } from "@/lib/format";

export interface ResultLocationState {
  result: CoarseGrainResult;
}

function readResult(state: unknown, workspaceId: string | undefined) {
  if (typeof state !== "object" || state === null || !("result" in state)) {
    return null;
  }
  const { result } = state as ResultLocationState;
  return result.workspace_id === workspaceId ? result : null;
}

export function ResultPage() {
  const { workspaceId } = useParams();
  const location = useLocation();
  const result = readResult(location.state, workspaceId);

  if (!result) {
    return (
      <PageHero
        eyebrow="Result"
        title={
          <>
            Result <span className="text-accent">not available</span>
          </>
        }
      >
        <p>
          Results are only available right after processing. Please coarse-grain the
          structure again.
        </p>
        <Link to="/" className="mt-4 inline-block text-accent hover:text-accent-hover">
          ← New structure
        </Link>
      </PageHero>
    );
  }

  const { atom_counts: atomCounts, files, model } = result;
  const downloadName = `${result.filename}_${model.name}`;
  const reportRows = [
    ["Model", model.name],
    ["Resolution", formatBeadsPerResidue(model.beads_per_residue)],
    ["Reference atoms", atomCounts.original.toLocaleString("en-US")],
    ["Coarse-grained beads", atomCounts.coarse.toLocaleString("en-US")],
    ["Atom reduction", formatPercent(atomCounts.reduction)],
    ["Models", result.selected_models.join(", ") || "All"],
    ["Chains", result.selected_chains.join(", ") || "All"],
  ] as const;

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
          {files.coarse_pdb_url && (
            <a
              href={files.coarse_pdb_url}
              download={`${downloadName}.pdb`}
              className={buttonClasses("primary")}
            >
              Download PDB
            </a>
          )}
          <a
            href={files.coarse_mmcif_url}
            download={`${downloadName}.cif`}
            className={buttonClasses(files.coarse_pdb_url ? "ghost" : "primary")}
          >
            Download mmCIF
          </a>
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[3fr_2fr]">
        <div className="flex min-h-80 items-center justify-center rounded-md bg-blue-ink">
          <p className="font-mono text-label tracking-[0.15em] text-white/60 uppercase">
            Structure viewer
          </p>
        </div>

        <section className="rounded-md border border-line-soft bg-white p-5">
          <h2 className="eyebrow">Model report</h2>
          <dl className="mt-3">
            {reportRows.map(([label, value]) => (
              <div
                key={label}
                className="flex justify-between gap-4 border-b border-dashed border-line-soft py-2 last:border-b-0"
              >
                <dt className="font-mono text-label tracking-[0.15em] text-ink-3 uppercase">
                  {label}
                </dt>
                <dd className="text-right font-mono text-sm text-ink">{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </div>
  );
}
