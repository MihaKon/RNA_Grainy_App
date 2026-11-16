import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { CIF } from "molstar/lib/mol-io/reader/cif";
import { trajectoryFromMmCIF } from "molstar/lib/mol-model-formats/structure/mmcif";
import { StructConn } from "molstar/lib/mol-model-formats/structure/property/bonds/struct_conn";
import { describe, expect, it } from "vitest";

import { createDefaultDraft, type ModelDraft } from "./modelDraft";
import { atomicMass } from "./nucleotideDiagram";
import {
  buildPreview,
  type PreviewResidue,
  readPreviewSource,
} from "./previewStructure";

async function parse(text: string) {
  const parsed = await CIF.parseText(text).run();
  if (parsed.isError) throw new Error(parsed.message);
  const block = parsed.result.blocks[0];
  if (!block) throw new Error("No CIF block.");
  return block;
}

const source: PreviewResidue[] = [
  {
    base: "A",
    chain: "A",
    sequence: 1,
    atoms: [
      { name: "P", element: "P", x: 0, y: 2, z: 4 },
      { name: "OP1", element: "O", x: 4, y: 6, z: 8 },
      { name: "C4'", element: "C", x: 10, y: 11, z: 12 },
    ],
  },
];

function draft(strategy: "direct" | "geometric_center" | "center_of_mass"): ModelDraft {
  return {
    ...createDefaultDraft(),
    beads: [
      {
        key: "test",
        beadId: "A1",
        name: "center",
        scope: "phosphate",
        strategy,
        description: "",
        atoms: strategy === "direct" ? ["P"] : ["P", "OP1"],
      },
    ],
    intraResidue: [],
    interResidue: { source: null, target: null },
  };
}

describe("creator preview structures", () => {
  it("counts only residues that produce beads in the selected preview", () => {
    const residue = source[0];
    if (!residue) throw new Error("Missing fixture");
    const model = draft("direct");
    model.beads = model.beads.map((bead) => ({ ...bead, scope: "adenine" }));
    const residues: PreviewResidue[] = [
      residue,
      {
        ...residue,
        sequence: 2,
        atoms: residue.atoms.filter((atom) => atom.name !== "P"),
      },
      { ...residue, base: "C", sequence: 3 },
    ];
    expect(buildPreview(model, residues, "all").atomCounts).toEqual({
      original: 3,
      coarse: 1,
      reduction: 1 - 1 / 3,
    });
    expect(buildPreview(model, residues, "C").atomCounts).toEqual({
      original: 0,
      coarse: 0,
      reduction: 0,
    });
  });

  it("counts accepted alternate conformations from the first model only", async () => {
    const parsed = await readPreviewSource(`data_alternates
loop_
_entity.id
_entity.type
1 polymer
loop_
_atom_site.label_entity_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.label_comp_id
_atom_site.label_alt_id
_atom_site.label_atom_id
_atom_site.type_symbol
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.pdbx_PDB_model_num
1 A 1 A . P P 0 0 0 1
1 A 1 A A OP1 O 1 0 0 1
1 A 1 A ? OP2 O 0 1 0 1
1 A 1 A B OP1 O 2 0 0 1
1 A 1 A C OP2 O 0 2 0 1
1 A 2 A B P P 3 0 0 1
1 A 1 A . P P 4 0 0 2
`);
    expect(parsed.residues).toHaveLength(1);
    expect(parsed.residues[0]?.inputAtomCount).toBe(3);
    expect(
      buildPreview(draft("direct"), parsed.residues, "all").atomCounts.original,
    ).toBe(3);
  });

  it("calculates all mapping strategies using experimental coordinates", async () => {
    for (const strategy of ["direct", "geometric_center", "center_of_mass"] as const) {
      const preview = buildPreview(draft(strategy), source, "all");
      const site = (await parse(preview.coarse)).categories.atom_site;
      const expected =
        strategy === "direct"
          ? 0
          : strategy === "geometric_center"
            ? 2
            : (4 * atomicMass("O")) / (atomicMass("P") + atomicMass("O"));
      expect(site?.getField("Cartn_x")?.float(0)).toBeCloseTo(expected, 3);
      expect(site?.rowCount).toBe(1);
    }
  });

  it.each(["1EHZ", "1MNX", "2F8S"])(
    "loads %s and produces Molstar-readable atoms and explicit bonds",
    async (id) => {
      const text = readFileSync(
        resolve(import.meta.dirname, "../../../../app/static/presets", `${id}.cif`),
        "utf8",
      );
      const source = await readPreviewSource(text);
      const residues = source.residues;
      const preview = buildPreview(createDefaultDraft(), residues, "all");
      const expected = (
        { "1EHZ": [1652, 380], "1MNX": [1364, 209], "2F8S": [930, 220] } as Record<
          string,
          number[]
        >
      )[id];
      expect(preview.atomCounts.original).toBe(expected?.[0]);
      expect(preview.atomCounts.coarse).toBe(expected?.[1]);
      expect(preview.atomCounts.reduction).toBeCloseTo(
        1 - preview.count / preview.atomCounts.original,
      );
      expect(preview.count).toBe(residues.length * 5 - (id === "1MNX" ? 1 : 0));
      const block = await parse(preview.coarse);
      const model = (await trajectoryFromMmCIF(block).run()).representative;
      expect(model.atomicHierarchy.atoms._rowCount).toBe(preview.count);
      expect(StructConn.Provider.get(model)?.entries).toHaveLength(
        block.categories.struct_conn?.rowCount ?? 0,
      );
      expect(StructConn.Provider.get(model)?.entries.length).toBeGreaterThan(
        preview.count,
      );
      const single = buildPreview(createDefaultDraft(), residues, "A");
      expect(single.residueCount).toBe(1);
      expect(single.count).toBe(5);
      expect((await readPreviewSource(single.reference)).residues[0]?.base).toBe("A");
    },
  );

  it("does not bridge missing residues or different chains", async () => {
    const atom = source[0];
    if (!atom) throw new Error("Missing fixture.");
    const model = draft("direct");
    model.interResidue = { source: "A1", target: "A1" };
    const preview = buildPreview(
      model,
      [atom, { ...atom, sequence: 3 }, { ...atom, chain: "B", sequence: 4 }],
      "all",
    );
    expect((await parse(preview.coarse)).categories.struct_conn).toBeUndefined();
  });

  it("keeps quoted atom names readable", async () => {
    const model = draft("direct");
    model.beads = model.beads.map((bead) => ({ ...bead, name: `C' "center"` }));
    const preview = buildPreview(model, source, "all");
    expect(
      (await parse(preview.coarse)).categories.atom_site
        ?.getField("label_atom_id")
        ?.str(0),
    ).toBe(`C' "center"`);
  });
});
