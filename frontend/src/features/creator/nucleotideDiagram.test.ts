import { describe, expect, it } from "vitest";

import { ALL_RESIDUES, residuesForScope } from "./atoms";
import { createDefaultDraft } from "./modelDraft";
import { beadLabels, nucleotideDiagram } from "./nucleotideDiagram";

describe("bead label placement", () => {
  it.each(ALL_RESIDUES)(
    "keeps labels clear of atoms and other labels in %s",
    (base) => {
      const draft = createDefaultDraft();
      const { atoms } = nucleotideDiagram(base);
      const template = draft.beads[0];
      if (!template) throw new Error("Missing bead fixture");
      const layouts = [
        draft.beads.filter((bead) => residuesForScope(bead.scope).includes(base)),
        Object.keys(atoms)
          .slice(0, 12)
          .map((atom, index) => ({
            ...template,
            key: `dense-${index.toString()}`,
            beadId: `B${index.toString()}`,
            atoms: [atom],
          })),
      ];
      for (const beads of layouts) {
        const labels = beadLabels(beads, atoms);
        expect(beadLabels(beads, atoms)).toEqual(labels);
        labels.forEach(({ label: [x, y] }, index) => {
          expect(x).toBeGreaterThanOrEqual(8);
          expect(x + 36).toBeLessThanOrEqual(382);
          expect(y).toBeGreaterThanOrEqual(32);
          expect(y + 20).toBeLessThanOrEqual(266);
          for (const [name, [ax, ay]] of Object.entries(atoms)) {
            const halfWidth = Math.max(15, (name.length * 7 + 4) / 2);
            expect(
              x + 36 <= ax - halfWidth ||
                x >= ax + halfWidth ||
                y + 20 <= ay - 13 ||
                y >= ay + 13,
            ).toBe(true);
          }
          labels.slice(index + 1).forEach(({ label: [otherX, otherY] }) => {
            expect(
              x + 40 <= otherX ||
                otherX + 40 <= x ||
                y + 24 <= otherY ||
                otherY + 24 <= y,
            ).toBe(true);
          });
        });
      }
    },
  );
});
