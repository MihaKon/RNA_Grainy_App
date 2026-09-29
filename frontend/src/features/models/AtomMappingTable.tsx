import type { ResidueMapping } from "@/api/types";

import { groupMapping } from "./mappingGroups";

export function AtomMappingTable({ mapping }: { mapping: readonly ResidueMapping[] }) {
  return (
    <div className="flex flex-col gap-4">
      {groupMapping(mapping).map(({ residueType, residues, beads }) => (
        <section
          key={`${residueType}-${residues.join()}`}
          className="rounded-md border border-line-soft"
        >
          <h4 className="flex items-baseline gap-2 border-b border-dashed border-line-soft px-4 py-2">
            <span className="text-sm font-medium text-ink">{residueType}</span>
            <span className="font-mono text-xs text-ink-3">{residues.join(", ")}</span>
          </h4>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line-soft">
                {["Bead ID", "Bead", "Description"].map((heading) => (
                  <th
                    key={heading}
                    scope="col"
                    className="px-4 py-2 font-mono text-label font-normal tracking-[0.15em] text-ink-3 uppercase"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {beads.map((bead) => (
                <tr
                  key={bead.bead_id}
                  className="border-b border-dashed border-line-soft last:border-b-0"
                >
                  <td className="px-4 py-2 font-mono text-accent">{bead.bead_id}</td>
                  <td className="px-4 py-2 font-mono text-ink">{bead.bead}</td>
                  <td className="px-4 py-2 text-ink-2">{bead.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}
