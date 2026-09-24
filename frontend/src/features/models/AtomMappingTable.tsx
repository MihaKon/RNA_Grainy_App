import type { ResidueMapping } from "@/api/types";

export function AtomMappingTable({ mapping }: { mapping: readonly ResidueMapping[] }) {
  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b border-ink/20">
          {["Residue", "Bead", "Atom", "Description"].map((heading) => (
            <th
              key={heading}
              scope="col"
              className="py-2 pr-3 font-mono text-label font-normal tracking-[0.15em] text-ink-3 uppercase"
            >
              {heading}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {mapping.flatMap(({ residue, residue_type: residueType, beads }) =>
          beads.map((bead, index) => (
            <tr
              key={`${residue}-${bead.bead_id}`}
              className="border-b border-dashed border-line-soft last:border-b-0"
            >
              {index === 0 && (
                <th
                  scope="rowgroup"
                  rowSpan={beads.length}
                  className="py-2 pr-3 align-top font-normal"
                >
                  <span className="font-mono text-ink">{residue}</span>
                  <span className="block text-xs text-ink-3">{residueType}</span>
                </th>
              )}
              <td className="py-2 pr-3 font-mono text-accent">{bead.bead_id}</td>
              <td className="py-2 pr-3 font-mono text-ink">{bead.bead}</td>
              <td className="py-2 text-ink-2">{bead.description}</td>
            </tr>
          )),
        )}
      </tbody>
    </table>
  );
}
