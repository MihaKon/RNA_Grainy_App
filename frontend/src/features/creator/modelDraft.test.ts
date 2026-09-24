import { describe, expect, it } from "vitest";

import {
  createDefaultDraft,
  type DraftAction,
  draftReducer,
  fromDefinition,
  type ModelDraft,
  toDefinition,
  validateDraft,
} from "./modelDraft";

const withoutKeys = (draft: ModelDraft) => ({
  ...draft,
  beads: draft.beads
    .map(({ key, ...bead }) => bead)
    .sort((a, b) => `${a.beadId}:${a.scope}`.localeCompare(`${b.beadId}:${b.scope}`)),
});

function reduce(draft: ModelDraft, ...actions: DraftAction[]): ModelDraft {
  return actions.reduce(draftReducer, draft);
}

function beadKey(draft: ModelDraft, beadId: string, index = 0): string {
  const bead = draft.beads.filter((candidate) => candidate.beadId === beadId)[index];
  if (!bead) throw new Error(`No bead ${beadId}`);
  return bead.key;
}

describe("toDefinition", () => {
  it("builds the same definition as the previous creator for the default model", () => {
    const config = (entries: [string, string, string][]) => ({
      bead_names: Object.fromEntries(entries.map(([id, name]) => [id, name])),
      atom_centers: Object.fromEntries(entries.map(([id, , atom]) => [id, [atom]])),
      description: Object.fromEntries(entries.map(([id]) => [id, ""])),
      strategies: Object.fromEntries(entries.map(([id]) => [id, "direct"])),
    });

    expect(toDefinition(createDefaultDraft())).toEqual({
      model_name: "Custom Model",
      description: "Custom Model based on SimRNA.",
      default_mapping: {
        residues: ["A", "G", "C", "U"],
        config: config([
          ["A1", "P", "P"],
          ["A2", "C4", "C4'"],
          ["A4", "C2", "C2"],
        ]),
      },
      mapping: [
        {
          residues: ["A", "G"],
          config: config([
            ["A3", "N9", "N9"],
            ["A5", "C6", "C6"],
          ]),
        },
        {
          residues: ["C", "U"],
          config: config([
            ["A3", "N1", "N1"],
            ["A5", "C4", "C4"],
          ]),
        },
      ],
      connectivity: {
        intra_residue: [
          ["A1", "A2"],
          ["A2", "A3"],
          ["A3", "A4"],
          ["A4", "A5"],
          ["A5", "A3"],
        ],
        inter_residue: [{ source: "A5", target: "A1" }],
      },
    });
  });

  it("omits an incomplete inter-residue connection", () => {
    const draft = reduce(createDefaultDraft(), { type: "clearInterConnection" });
    expect(toDefinition(draft).connectivity.inter_residue).toEqual([]);
  });
});

describe("fromDefinition", () => {
  it("round-trips a definition built by the creator", () => {
    const draft = createDefaultDraft();
    const definition = JSON.parse(JSON.stringify(toDefinition(draft))) as Record<
      string,
      unknown
    >;

    expect(withoutKeys(fromDefinition(definition))).toEqual(withoutKeys(draft));
  });

  it("tolerates missing and malformed sections", () => {
    const draft = fromDefinition({
      default_mapping: {
        residues: ["A", "G", "C", "U"],
        config: { bead_names: { B1: "P", B2: 3 }, strategies: { B1: "unknown" } },
      },
      connectivity: { intra_residue: [["B1"], ["B1", "B2"]], inter_residue: [] },
    });

    expect(withoutKeys(draft)).toEqual({
      name: "Imported Model",
      description: "",
      beads: [
        {
          beadId: "B1",
          name: "P",
          scope: "all",
          strategy: "direct",
          description: "",
          atoms: [],
        },
      ],
      intraResidue: [["B1", "B2"]],
      interResidue: { source: null, target: null },
    });
  });
});

describe("draftReducer", () => {
  it("adds beads with the next free ID", () => {
    const draft = reduce(
      createDefaultDraft(),
      { type: "addBead" },
      { type: "addBead" },
    );
    expect(draft.beads.slice(-2).map((bead) => bead.beadId)).toEqual(["A8", "A9"]);
  });

  it("keeps connections while another bead still uses the removed ID", () => {
    let draft = createDefaultDraft();
    draft = reduce(draft, { type: "removeBead", key: beadKey(draft, "A3") });
    expect(draft.intraResidue).toContainEqual(["A2", "A3"]);

    draft = reduce(draft, { type: "removeBead", key: beadKey(draft, "A3") });
    expect(draft.intraResidue.flat()).not.toContain("A3");
  });

  it("clears the inter-residue connection of a removed bead", () => {
    let draft = createDefaultDraft();
    draft = reduce(draft, { type: "removeBead", key: beadKey(draft, "A1") });
    expect(draft.interResidue).toEqual({ source: null, target: null });
  });

  it("moves connections along with a renamed bead ID", () => {
    let draft = createDefaultDraft();
    draft = reduce(draft, {
      type: "renameBead",
      key: beadKey(draft, "A1"),
      beadId: "P1",
    });

    expect(draft.intraResidue[0]).toEqual(["P1", "A2"]);
    expect(draft.interResidue).toEqual({ source: "A5", target: "P1" });
  });

  it("leaves connections alone when a shared bead ID is renamed", () => {
    let draft = createDefaultDraft();
    draft = reduce(draft, {
      type: "renameBead",
      key: beadKey(draft, "A3"),
      beadId: "B3",
    });

    expect(draft.intraResidue).toContainEqual(["A2", "A3"]);
  });

  it("allows a single atom for direct mapping and several otherwise", () => {
    let draft = createDefaultDraft();
    const key = beadKey(draft, "A4");

    draft = reduce(draft, { type: "toggleAtom", key, atom: "N3" });
    expect(draft.beads.find((bead) => bead.key === key)?.atoms).toEqual(["N3"]);

    draft = reduce(
      draft,
      { type: "setBeadStrategy", key, strategy: "geometric_center" },
      { type: "toggleAtom", key, atom: "C4" },
    );
    expect(draft.beads.find((bead) => bead.key === key)?.atoms).toEqual(["N3", "C4"]);

    draft = reduce(draft, { type: "setBeadStrategy", key, strategy: "direct" });
    expect(draft.beads.find((bead) => bead.key === key)?.atoms).toEqual(["N3"]);
  });

  it("toggles intra-residue connections in either direction", () => {
    let draft = reduce(createDefaultDraft(), {
      type: "toggleIntraConnection",
      first: "A2",
      second: "A1",
    });
    expect(draft.intraResidue).not.toContainEqual(["A1", "A2"]);

    draft = reduce(draft, { type: "toggleIntraConnection", first: "A1", second: "A1" });
    draft = reduce(draft, { type: "toggleIntraConnection", first: "A1", second: "A4" });
    expect(draft.intraResidue).toContainEqual(["A1", "A4"]);
    expect(draft.intraResidue.flat()).not.toContain(undefined);
  });
});

describe("validateDraft", () => {
  it("accepts the default model", () => {
    expect(validateDraft(createDefaultDraft())).toEqual({ beads: {}, model: [] });
  });

  it("reports beads without atoms and overlapping bead IDs", () => {
    let draft = reduce(createDefaultDraft(), { type: "addBead" });
    const newBead = draft.beads.at(-1)?.key ?? "";
    draft = reduce(draft, { type: "renameBead", key: newBead, beadId: "A1" });

    expect(validateDraft(draft).beads[newBead]).toEqual([
      "Select at least one atom.",
      "Bead A1 is already defined for A, G, C, U.",
    ]);
  });

  it("requires both ends of the inter-residue connection", () => {
    const draft = reduce(
      createDefaultDraft(),
      { type: "clearInterConnection" },
      { type: "setInterConnection", end: "source", beadId: "A5" },
    );

    expect(validateDraft(draft).model).toEqual([
      "Choose both beads of the inter-residue connection.",
    ]);
  });
});
