const DEFAULT_MODEL = {
  name: "Custom Model",
  description:
    "Custom Model based on SimRNA.",
  beads: [
    {
      beadID: "A1",
      name: "P",
      scope: "phosphate",
      strategy: "direct",
      atoms: ["P"],
    },
    {
      beadID: "A2",
      name: "C4",
      scope: "sugar",
      strategy: "direct",
      atoms: ["C4'"],
    },
    {
      beadID: "A3",
      name: "N9",
      scope: "purine",
      strategy: "direct",
      atoms: ["N9"],
    },
    {
      beadID: "A3",
      name: "N1",
      scope: "pyrimidine",
      strategy: "direct",
      atoms: ["N1"],
    },
    {
      beadID: "A4",
      name: "C2",
      scope: "all",
      strategy: "direct",
      atoms: ["C2"],
    },
    {
      beadID: "A5",
      name: "C6",
      scope: "purine",
      strategy: "direct",
      atoms: ["C6"],
    },
    {
      beadID: "A5",
      name: "C4",
      scope: "pyrimidine",
      strategy: "direct",
      atoms: ["C4"],
    },
  ],

  intra_residues: [
    ["A1", "A2"],
    ["A2", "A3"],
    ["A3", "A4"],
    ["A4", "A5"],
    ["A5", "A3"],
  ],
  inter_residues: [{ source: "A5", target: "A1" }],
};
