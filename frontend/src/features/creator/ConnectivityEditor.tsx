import { ArrowRight, Link2 } from "lucide-react";
import type { Dispatch } from "react";

import { Button } from "@/components/ui/Button";
import { ToggleButton } from "@/components/ui/ToggleButton";
import { cn } from "@/lib/cn";

import { ChipGroup } from "./ChipGroup";
import {
  type DraftAction,
  hasIntraConnection,
  type InterResidueDraft,
  type ModelDraft,
  uniqueBeadIds,
} from "./modelDraft";

interface ConnectivityEditorProps {
  draft: ModelDraft;
  dispatch: Dispatch<DraftAction>;
}

const INTER_ENDS: readonly { end: keyof InterResidueDraft; legend: string }[] = [
  { end: "source", legend: "Residue i (source)" },
  { end: "target", legend: "Residue i+1 (target)" },
];

export function ConnectivityEditor({ draft, dispatch }: ConnectivityEditorProps) {
  const beadIds = uniqueBeadIds(draft).filter(Boolean);
  const { source, target } = draft.interResidue;

  return (
    <div className="flex flex-col gap-8">
      <section aria-labelledby="intra-residue-heading" className="flex flex-col gap-3">
        <div>
          <h3
            id="intra-residue-heading"
            className="text-sm font-medium text-ink uppercase"
          >
            Intra-residue connections
          </h3>
          <p className="text-xs text-ink-3">
            Select pairs of beads that are bonded within a single residue.
          </p>
        </div>
        <div className="overflow-x-auto rounded-md border border-line-soft bg-white p-3">
          <table className="font-mono text-xs">
            <thead>
              <tr>
                <td />
                {beadIds.map((beadId) => (
                  <th
                    key={beadId}
                    scope="col"
                    className="px-1 pb-2 font-normal text-ink-2"
                  >
                    {beadId}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {beadIds.map((rowId, row) => (
                <tr key={rowId}>
                  <th scope="row" className="pr-3 text-right font-normal text-ink-2">
                    {rowId}
                  </th>
                  {beadIds.map((columnId, column) => {
                    if (column <= row) return <td key={columnId} />;
                    const connected = hasIntraConnection(draft, rowId, columnId);
                    return (
                      <td key={columnId} className="p-0.5">
                        <button
                          type="button"
                          aria-pressed={connected}
                          aria-label={`Connect ${rowId} and ${columnId}`}
                          onClick={() => {
                            dispatch({
                              type: "toggleIntraConnection",
                              first: rowId,
                              second: columnId,
                            });
                          }}
                          className={cn(
                            "flex size-8 items-center justify-center rounded border-[1.5px] transition-colors",
                            connected
                              ? "border-accent bg-accent text-white"
                              : "border-line-soft bg-surface hover:border-accent",
                          )}
                        >
                          {connected && (
                            <Link2 aria-hidden="true" className="size-3.5" />
                          )}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="inter-residue-heading" className="flex flex-col gap-4">
        <div>
          <h3
            id="inter-residue-heading"
            className="text-sm font-medium text-ink uppercase"
          >
            Inter-residue connection
          </h3>
          <p className="text-xs text-ink-3">
            Links a bead of residue i with a bead of the next residue. Only one
            connection is supported.
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          {INTER_ENDS.map(({ end, legend }) => (
            <ChipGroup key={end} legend={legend}>
              {beadIds.map((beadId) => (
                <ToggleButton
                  key={beadId}
                  pressed={draft.interResidue[end] === beadId}
                  onClick={() => {
                    dispatch({ type: "setInterConnection", end, beadId });
                  }}
                >
                  {beadId}
                </ToggleButton>
              ))}
            </ChipGroup>
          ))}
        </div>

        <div className="flex items-center justify-between gap-3 rounded border border-dashed border-line-soft px-4 py-3">
          {source || target ? (
            <p className="flex items-center gap-2 font-mono text-sm text-ink">
              {source ?? "?"}
              <ArrowRight aria-label="to" className="size-3.5 text-ink-3" />
              {target ?? "?"}
            </p>
          ) : (
            <p className="text-sm text-ink-3">No inter-residue connection.</p>
          )}
          {(source ?? target) && (
            <Button
              variant="ghost"
              onClick={() => {
                dispatch({ type: "clearInterConnection" });
              }}
            >
              Clear
            </Button>
          )}
        </div>
      </section>
    </div>
  );
}
