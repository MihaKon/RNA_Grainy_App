import { describe, expect, it } from "vitest";

import {
  createDefaultDraft,
  type DraftAction,
  draftReducer,
  fromDefinition,
  type ModelDraft,
  positionConflict,
  resolveBeads,
  toDefinition,
  validateDraft,
} from "./modelDraft";

function requiredBead(draft: ModelDraft, index: number) {
  const bead = draft.beads.at(index);
  if (!bead) throw new Error("Missing test bead");
  return bead;
}

describe("exclusive bead positions", () => {
  it("changes scope and selects an atom without rejecting a valid final center", () => {
    const bead = {
      ...requiredBead(createDefaultDraft(), 0),
      scope: "purine" as const,
      strategy: "geometric_center" as const,
      atoms: ["O4'", "N9"],
    };
    const occupied = {
      ...bead,
      key: "occupied",
      beadId: "B2",
      name: "B2",
      scope: "nucleotide" as const,
      strategy: "direct" as const,
      atoms: ["O4'"],
    };
    const draft = { ...createDefaultDraft(), beads: [bead, occupied] };
    const changed = draftReducer(draft, {
      type: "setBeadScope",
      key: bead.key,
      scope: "pyrimidine",
      keepAtoms: true,
      atom: "N1",
    });
    expect(changed.beads[0]).toMatchObject({
      scope: "pyrimidine",
      atoms: ["O4'", "N1"],
    });
    expect(positionConflict(changed, requiredBead(changed, 0))).toBeUndefined();
    expect(
      draftReducer(draft, {
        type: "setBeadScope",
        key: bead.key,
        scope: "pyrimidine",
        atom: "O4'",
      }),
    ).toBe(draft);
  });
  it.each(["direct", "geometric_center", "center_of_mass"] as const)(
    "rejects an occupied atom with %s mapping",
    (strategy) => {
      const draft = draftReducer(createDefaultDraft(), { type: "addBead", strategy });
      const bead = requiredBead(draft, -1);
      expect(
        draftReducer(draft, { type: "toggleAtom", key: bead.key, atom: "P" }),
      ).toBe(draft);
      const free = draftReducer(draft, {
        type: "toggleAtom",
        key: bead.key,
        atom: "OP1",
      });
      expect(free.beads.at(-1)?.atoms).toEqual(["OP1"]);
    },
  );

  it("validates duplicate centers regardless of atom order", () => {
    const first = {
      ...requiredBead(createDefaultDraft(), 0),
      strategy: "geometric_center" as const,
      atoms: ["OP1", "OP2"],
    };
    const second = {
      ...first,
      key: "second",
      beadId: "B2",
      name: "B2",
      atoms: ["OP2", "OP1"],
    };
    const draft = { ...createDefaultDraft(), beads: [first, second] };
    expect(positionConflict(draft, second)).toContain("A1");
    expect(validateDraft(draft).beads[second.key]).toContain(
      "Position already occupied by bead A1 in A.",
    );
    const edited = draftReducer(draft, {
      type: "updateBead",
      key: second.key,
      patch: { description: "Imported center" },
    });
    expect(edited.beads.find((bead) => bead.key === second.key)?.description).toBe(
      "Imported center",
    );
    expect(validateDraft(edited).beads[second.key]).toBeDefined();
  });

  it("allows equal positions on disjoint bases and rejects expanding into an occupied base", () => {
    const first = {
      ...requiredBead(createDefaultDraft(), 0),
      scope: "adenine" as const,
    };
    const second = {
      ...first,
      key: "second",
      beadId: "B2",
      name: "B2",
      scope: "guanine" as const,
    };
    const draft = { ...createDefaultDraft(), beads: [first, second] };
    expect(positionConflict(draft, second)).toBeUndefined();
    expect(
      draftReducer(draft, {
        type: "setBeadScope",
        key: second.key,
        scope: "purine",
        keepAtoms: true,
      }),
    ).toBe(draft);
  });

  it("allows reusing a position after removing its bead", () => {
    const draft = draftReducer(createDefaultDraft(), { type: "addBead" });
    const bead = requiredBead(draft, -1);
    const removed = draftReducer(draft, {
      type: "removeBead",
      key: requiredBead(draft, 0).key,
    });
    expect(
      draftReducer(removed, { type: "toggleAtom", key: bead.key, atom: "P" }).beads.at(
        -1,
      )?.atoms,
    ).toEqual(["P"]);
  });
});

const withoutKeys = (draft: ModelDraft) => ({
  ...draft,
  beads: draft.beads
    .map(({ key, ...bead }) => bead)
    .sort((a, b) => `${a.beadId}:${a.scope}`.localeCompare(`${b.beadId}:${b.scope}`)),
});

const BUILT_IN_MODELS = Object.fromEntries(
  Object.entries(
    import.meta.glob<Record<string, unknown>>(
      "../../../../app/coarse_grain/models/*.json",
      {
        eager: true,
        import: "default",
      },
    ),
  ).map(([path, definition]) => [path.split("/").at(-1) ?? path, definition]),
);

const toJson = (definition: unknown) =>
  JSON.parse(JSON.stringify(definition)) as Record<string, unknown>;

function reduce(draft: ModelDraft, ...actions: DraftAction[]): ModelDraft {
  return actions.reduce(draftReducer, draft);
}

function beadKey(draft: ModelDraft, beadId: string, index = 0): string {
  const bead = draft.beads.filter((candidate) => candidate.beadId === beadId)[index];
  if (!bead) throw new Error(`No bead ${beadId}`);
  return bead.key;
}

describe("toDefinition", () => {
  it("builds the SimRNA definition for the default model", () => {
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
          ["A2", "C4'", "C4'"],
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
        inter_residue: [{ source: "A2", target: "A1" }],
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

  const mapping = (residues: string[], beads: Record<string, string[]>) => ({
    residues,
    config: {
      bead_names: Object.fromEntries(Object.keys(beads).map((id) => [id, id])),
      atom_centers: beads,
    },
  });

  it("resolves residue-specific overrides of the default mapping", () => {
    const draft = fromDefinition({
      default_mapping: mapping(["A", "G", "C", "U"], { A3: ["N1"] }),
      mapping: [mapping(["A", "G"], { A3: ["N9"] })],
    });

    expect(draft.beads.map(({ scope, atoms }) => [scope, atoms])).toEqual([
      ["purine", ["N9"]],
      ["pyrimidine", ["N1"]],
    ]);
    expect(validateDraft(draft).beads).toEqual({});
  });

  it("keeps overrides that change only the atoms of a default bead", () => {
    const draft = fromDefinition({
      default_mapping: mapping(["A", "G", "C", "U"], { A3: ["C2"] }),
      mapping: [{ residues: ["A", "G"], config: { atom_centers: { A3: ["N9"] } } }],
    });

    expect(
      draft.beads.map(({ beadId, scope, atoms }) => [beadId, scope, atoms]),
    ).toEqual([
      ["A3", "purine", ["N9"]],
      ["A3", "pyrimidine", ["C2"]],
    ]);
  });

  it("splits residue sets without a scope into one bead per residue", () => {
    const definition = {
      default_mapping: mapping(["A", "G", "C", "U"], { A1: ["P"] }),
      mapping: [mapping(["A", "C"], { A2: ["N1"] })],
    };
    const draft = fromDefinition(definition);

    expect(draft.beads.map(({ beadId, scope }) => [beadId, scope])).toEqual([
      ["A1", "phosphate"],
      ["A2", "adenine"],
      ["A2", "cytosine"],
    ]);
    expect(resolveBeads(toJson(toDefinition(draft)))).toEqual(resolveBeads(definition));
  });

  it("splits beads that use atoms only some of their residues have", () => {
    const definition = {
      default_mapping: mapping(["A", "G", "C", "U"], { A1: ["P"] }),
      mapping: [
        {
          residues: ["C", "U"],
          config: {
            bead_names: { A3: "PY" },
            atom_centers: { A3: ["N3", "N4", "O4"] },
            strategies: { A3: "center_of_mass" },
          },
        },
        mapping(["A", "G"], { A2: ["N6"] }),
      ],
    };
    const draft = fromDefinition(definition);

    expect(
      draft.beads.map(({ beadId, scope, atoms }) => [beadId, scope, atoms]),
    ).toEqual([
      ["A1", "phosphate", ["P"]],
      ["A2", "adenine", ["N6"]],
      ["A3", "cytosine", ["N3", "N4"]],
      ["A3", "uracil", ["N3", "O4"]],
    ]);
    expect(validateDraft(draft).beads).toEqual({});
    expect(resolveBeads(toJson(toDefinition(draft)))).toEqual(resolveBeads(definition));
  });

  it("rejects residues the creator cannot edit", () => {
    expect(() =>
      fromDefinition({ default_mapping: mapping(["A", "PSU"], { A1: ["P"] }) }),
    ).toThrow("The creator supports residues A, G, C and U, not PSU.");
  });

  it.each(Object.entries(BUILT_IN_MODELS))(
    "keeps the meaning of %s through import and export",
    (_, definition) => {
      const exported = toJson(toDefinition(fromDefinition(definition)));
      expect(resolveBeads(exported)).toEqual(resolveBeads(definition));
    },
  );

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
    expect(draft.interResidue).toEqual({ source: "A2", target: "P1" });
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
    expect(validateDraft(createDefaultDraft())).toEqual({
      beads: {},
      model: [],
      invalidConnections: false,
    });
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

  it("reports bead names used twice in a residue", () => {
    let draft = reduce(createDefaultDraft(), { type: "addBead" });
    const newBead = draft.beads.at(-1)?.key ?? "";
    draft = reduce(
      draft,
      { type: "updateBead", key: newBead, patch: { name: "N9" } },
      { type: "setBeadScope", key: newBead, scope: "adenine" },
      { type: "toggleAtom", key: newBead, atom: "N7" },
    );

    expect(validateDraft(draft).beads[newBead]).toEqual([
      "Bead name N9 is already used for A.",
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

  it("reports imported direct beads with several atoms", () => {
    const definition = toDefinition(createDefaultDraft());
    definition.default_mapping.config.atom_centers.A1 = ["P", "OP1"];
    const draft = fromDefinition(toJson(definition));

    expect(validateDraft(draft).beads[beadKey(draft, "A1")]).toEqual([
      "Direct mapping uses exactly one atom.",
    ]);
  });

  it("reports atoms that some residues of the bead lack", () => {
    const draft = createDefaultDraft();
    const key = beadKey(draft, "A4");

    expect(
      validateDraft(reduce(draft, { type: "toggleAtom", key, atom: "N2" })).beads[key],
    ).toEqual(["N2 is missing from A, C, U."]);
  });

  it("reports connections to beads that some residues do not define", () => {
    let draft = reduce(createDefaultDraft(), { type: "addBead" });
    const newBead = draft.beads.at(-1)?.key ?? "";
    draft = reduce(
      draft,
      { type: "setBeadScope", key: newBead, scope: "purine" },
      { type: "toggleAtom", key: newBead, atom: "N7" },
      { type: "updateBead", key: newBead, patch: { name: "N7" } },
      { type: "toggleIntraConnection", first: "A2", second: "A8" },
      { type: "setInterConnection", end: "target", beadId: "A8" },
    );

    expect(validateDraft(draft)).toMatchObject({
      model: [
        "Connection A2–A8: bead A8 is not defined for C, U.",
        "Inter-residue connection A2 → A8: bead A8 is not defined for C, U.",
      ],
      invalidConnections: false,
    });
  });

  it("reports and removes invalid connections", () => {
    const definition = {
      ...toDefinition(createDefaultDraft()),
      connectivity: {
        intra_residue: [
          ["A1", "A2"],
          ["A1", "B9"],
          ["A3", "A3"],
          ["A2", "A1"],
        ],
        inter_residue: [{ source: "A5", target: "B9" }],
      },
    };
    const draft = fromDefinition(definition);

    expect(validateDraft(draft)).toMatchObject({
      model: [
        "Connection A1–B9 uses undefined bead B9.",
        "Connection A3–A3 connects a bead to itself.",
        "Connection A2–A1 is listed twice.",
        "Inter-residue connection A5 → B9 uses undefined bead B9.",
      ],
      invalidConnections: true,
    });

    const cleaned = reduce(draft, { type: "removeInvalidConnections" });
    expect(cleaned.intraResidue).toEqual([["A1", "A2"]]);
    expect(cleaned.interResidue).toEqual({ source: null, target: null });
    expect(validateDraft(cleaned)).toMatchObject({
      model: [],
      invalidConnections: false,
    });
  });
});
