import { Download } from "lucide-react";
import { useState } from "react";

import type { ConversionReport, ResidueConversion } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { downloadTextFile } from "@/lib/download";

export function ConversionLog({
  report,
  filename,
}: {
  report: ConversionReport | null | undefined;
  filename: string;
}) {
  const [visibleCount, setVisibleCount] = useState(50);

  return (
    <section
      aria-label="Conversion report"
      className="mt-4 min-w-0 rounded-md border border-line-soft bg-white p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="eyebrow">Conversion report</h2>
        {report && (
          <Button
            variant="text"
            onClick={() => {
              downloadTextFile(
                JSON.stringify(report, null, 2),
                `${filename}_conversion_report.json`,
              );
            }}
          >
            <Download aria-hidden="true" className="size-3" />
            Download report
          </Button>
        )}
      </div>
      {report ? (
        <>
          <ReportSummary report={report} />
          {report.estimated_atoms > 0 && (
            <p className="mt-2 text-sm text-ink-2">
              Estimated positions are approximations used for CG conversion. The input
              structure remains unchanged.
            </p>
          )}
          {report.residues.length === 0 && report.skipped_connections.length === 0 ? (
            <p className="mt-3 text-sm text-ink-2">
              No conversion issues or repairs reported.
            </p>
          ) : (
            <div className="mt-5 max-h-[32rem] space-y-5 overflow-y-auto overscroll-contain text-sm">
              {report.residues.length > 0 && (
                <div>
                  <h3 className="mb-2 eyebrow">Nucleotide details</h3>
                  <div className="space-y-2">
                    {report.residues.slice(0, visibleCount).map((entry, index) => (
                      <ResidueLog
                        key={`${String(entry.model)}-${entry.chain}-${entry.residue_id}-${String(index)}`}
                        entry={entry}
                      />
                    ))}
                  </div>
                </div>
              )}
              {report.skipped_connections.length > 0 && (
                <div>
                  <h3 className="eyebrow">Skipped connections</h3>
                  <p className="mt-1 mb-3 text-xs text-ink-3">
                    Connections longer than 8 Å were omitted. Their beads were retained.
                  </p>
                  <table
                    aria-label="Skipped connections"
                    className="w-full table-fixed text-left"
                  >
                    <thead className="border-b border-line-soft text-xs text-ink-3">
                      <tr>
                        <th scope="col" className="w-1/4 pb-2 font-medium">
                          Location
                        </th>
                        <th scope="col" className="pb-2 font-medium">
                          Bead pair
                        </th>
                        <th scope="col" className="w-20 pb-2 text-right font-medium">
                          Distance
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line-soft">
                      {report.skipped_connections
                        .slice(0, visibleCount)
                        .map((entry, index) => (
                          <tr key={`connection-${String(index)}`}>
                            <td className="py-3 pr-2 align-top text-xs wrap-anywhere text-ink-2">
                              Model {entry.model}
                              <br />
                              Chain {entry.chain}
                            </td>
                            <td className="py-3 pr-2 align-top font-mono text-xs wrap-anywhere text-ink">
                              {entry.source_residue}/{entry.source_bead} →{" "}
                              {entry.target_residue}/{entry.target_bead}
                            </td>
                            <td className="py-3 text-right align-top font-mono text-xs whitespace-nowrap text-ink">
                              {entry.distance.toFixed(2)} Å
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          {(report.residues.length > visibleCount ||
            report.skipped_connections.length > visibleCount) && (
            <Button
              variant="text"
              className="mt-3"
              onClick={() => {
                setVisibleCount((count) => count + 50);
              }}
            >
              Show more entries
            </Button>
          )}
        </>
      ) : (
        <p className="mt-3 text-sm text-ink-2">
          A conversion report is not available for this result.
        </p>
      )}
    </section>
  );
}

function ReportSummary({ report }: { report: ConversionReport }) {
  const metrics = [
    ["Created beads", report.created_beads, false],
    ["Estimated atoms", report.estimated_atoms, false],
    ["Mapped modifications", report.modified_residues, false],
    ["Skipped beads", report.skipped_beads, true],
    ["Skipped nucleotides", report.skipped_residues, true],
    ["Skipped connections", report.skipped_connections.length, true],
  ] as const;

  return (
    <>
      <p className="mt-3 text-xs text-ink-3">Totals across all selected input models</p>
      <dl className="mt-3 grid grid-cols-2 gap-2">
        {metrics.map(([label, count, omission]) => (
          <div
            key={label}
            className={cn(
              "flex min-w-0 flex-col-reverse gap-1 rounded border p-3",
              omission && count > 0
                ? "border-gold/60 bg-gold/10"
                : "border-line-soft bg-surface",
            )}
          >
            <dt className="text-xs text-ink-2">{label}</dt>
            <dd
              className={cn(
                "font-mono text-xl tabular-nums",
                count > 0 ? "text-ink" : "text-ink-3",
              )}
            >
              {count.toLocaleString("en-US")}
            </dd>
          </div>
        ))}
      </dl>
    </>
  );
}

function ResidueLog({ entry }: { entry: ResidueConversion }) {
  return (
    <div
      className={cn(
        "rounded border border-l-[3px] p-3 wrap-anywhere",
        entry.status === "skipped"
          ? "border-line-soft border-l-gold bg-gold/5"
          : "border-line-soft border-l-accent",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-medium text-ink">
            {entry.residue_name} {entry.residue_id}
          </p>
          <p className="mt-0.5 text-xs text-ink-3">
            Model {entry.model} · Chain {entry.chain}
          </p>
        </div>
        <span
          className={cn(
            "rounded px-2 py-1 text-xs font-medium",
            entry.status === "skipped"
              ? "bg-gold/20 text-ink"
              : "bg-accent/10 text-blue-deep",
          )}
        >
          {entry.status === "skipped"
            ? "Nucleotide skipped"
            : entry.estimated_atoms.length > 0
              ? "Atoms estimated"
              : entry.residue_name !== entry.canonical_name
                ? "Modified nucleotide"
                : "Conversion note"}
        </span>
      </div>
      <div className="mt-2 space-y-1 text-ink-2">
        {entry.residue_name !== entry.canonical_name && (
          <p>
            Modified nucleotide mapped: {entry.residue_name} → {entry.canonical_name}.
          </p>
        )}
        {entry.terminal_phosphate_absent && (
          <p>The first nucleotide has no phosphate group; it was not rebuilt.</p>
        )}
        {entry.ignored_altlocs.length > 0 && (
          <p>Alternate locations omitted: {entry.ignored_altlocs.join(", ")}.</p>
        )}
        {[...new Set(Object.values(entry.failures))].map((reason) => (
          <p key={reason}>{reason}</p>
        ))}
      </div>
      <dl className="mt-3 space-y-2 border-t border-dashed border-line-soft pt-2 text-xs">
        {(
          [
            ["Missing required atoms", entry.missing_atoms],
            ["Estimated atoms", entry.estimated_atoms],
            ["Created beads", entry.created_beads],
            ["Skipped beads", entry.skipped_beads],
          ] as const
        ).map(
          ([label, names]) =>
            names.length > 0 && (
              <div key={label}>
                <dt className="text-ink-3">{label}</dt>
                <dd className="mt-0.5 font-mono text-ink">{names.join(", ")}</dd>
              </div>
            ),
        )}
      </dl>
    </div>
  );
}
