import type { CoarseGrainResult } from "@/api/types";
import { formatBeadsPerResidue, formatPercent } from "@/lib/format";

export function ModelReport({ result }: { result: CoarseGrainResult }) {
  const { atom_counts: atomCounts, model } = result;
  const rows = [
    ["CG model", model.name],
    ["CG resolution", formatBeadsPerResidue(model.beads_per_residue, "nucleotide")],
    ["Input models", result.selected_models.join(", ") || "All"],
    ["Input chains", result.selected_chains.join(", ") || "All"],
    ["Input atoms", atomCounts.original.toLocaleString("en-US")],
    ["CG beads", atomCounts.coarse.toLocaleString("en-US")],
    ["Atom reduction", formatPercent(atomCounts.reduction)],
  ] as const;

  return (
    <section
      aria-labelledby="conversion-summary"
      className="rounded-md border border-line-soft bg-white p-5"
    >
      <h2 id="conversion-summary" className="eyebrow">
        Conversion summary
      </h2>
      <dl className="mt-3">
        {rows.map(([label, value]) => (
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
  );
}
