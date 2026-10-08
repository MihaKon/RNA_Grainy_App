import { describe, expect, it } from "vitest";

import type { ResidueMapping } from "@/api/types";

import { groupMapping } from "./mappingGroups";

const phosphate = { bead_id: "A1", bead: "P", description: "Phosphate P atom" };
const purineBase = { bead_id: "A2", bead: "B", description: "Purine base" };
const guanineBase = { bead_id: "A2", bead: "G", description: "Guanine base" };
const pyrimidineBase = { bead_id: "A2", bead: "B", description: "Pyrimidine base" };

describe("groupMapping", () => {
  it("shows residues of one type with identical beads once", () => {
    const mapping: ResidueMapping[] = [
      { residue: "A", residue_type: "Purine", beads: [phosphate, purineBase] },
      { residue: "G", residue_type: "Purine", beads: [phosphate, purineBase] },
      { residue: "C", residue_type: "Pyrimidine", beads: [phosphate, pyrimidineBase] },
      { residue: "U", residue_type: "Pyrimidine", beads: [phosphate, pyrimidineBase] },
    ];

    expect(groupMapping(mapping)).toEqual([
      { residueType: "Purine", residues: ["A", "G"], beads: [phosphate, purineBase] },
      {
        residueType: "Pyrimidine",
        residues: ["C", "U"],
        beads: [phosphate, pyrimidineBase],
      },
    ]);
  });

  it("keeps residues with different beads apart but next to their type", () => {
    const mapping: ResidueMapping[] = [
      { residue: "A", residue_type: "Purine", beads: [phosphate, purineBase] },
      { residue: "C", residue_type: "Pyrimidine", beads: [phosphate, pyrimidineBase] },
      { residue: "G", residue_type: "Purine", beads: [phosphate, guanineBase] },
    ];

    expect(
      groupMapping(mapping).map(({ residueType, residues }) => [residueType, residues]),
    ).toEqual([
      ["Purine", ["A"]],
      ["Purine", ["G"]],
      ["Pyrimidine", ["C"]],
    ]);
  });
});
