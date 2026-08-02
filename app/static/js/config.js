const ATOM_DEFINITIONS = {
  all: [
    "N1",
    "C2",
    "N3",
    "C4",
    "C5",
    "C6",
    "N2",
  ],
  phosphate: ["P", "OP1", "OP2"],
  sugar: ["C1'", "C2'", "C3'", "C4'", "C5'", "O2'", "O3'", "O4'", "O5'"],
  purine: [
    "N1",
    "C2",
    "N3",
    "C4",
    "C5",
    "C6",
    "N6",
    "N7",
    "C8",
    "N9",
    "N2",
    "O6",
  ],
  pyrimidine: ["N1", "C2", "O2", "N3", "C4", "N4", "C5", "C6", "O4"],
  adenine: ["N1", "C2", "N3", "C4", "C5", "C6", "N6", "N7", "C8", "N9"],
  guanine: ["N1", "C2", "N2", "N3", "C4", "C5", "C6", "O6", "N7", "C8", "N9"],
  cytosine: ["N1", "C2", "O2", "N3", "C4", "N4", "C5", "C6"],
  uracil: ["N1", "C2", "O2", "N3", "C4", "O4", "C5", "C6"],
};

const SCOPE_OPTIONS = [
  { value: "all", label: "All Bases" },
  { value: "phosphate", label: "Phosphate" },
  { value: "sugar", label: "Sugar" },
  { value: "purine", label: "Purines" },
  { value: "pyrimidine", label: "Pyrimidines" },
  { value: "adenine", label: "A" },
  { value: "cytosine", label: "C" },
  { value: "guanine", label: "G" },
  { value: "uracil", label: "U" },
];

const SCOPE_RESIDUES_MAP = {
  all: ["A", "G", "C", "U"],
  purine: ["A", "G"],
  pyrimidine: ["C", "U"],
  adenine: ["A"],
  cytosine: ["C"],
  guanine: ["G"],
  uracil: ["U"],
};

const STRATEGY_OPTIONS = [
  { value: "direct", label: "Direct Mapping" },
  { value: "center_of_mass", label: "Center of Mass" },
  { value: "geometric_center", label: "Geometric Center" },
];

const DEFAULT_MODEL = {
  name: "Custom Model",
  description: "Custom Model based on SimRNA.",
  beads: [
    { beadID: "A1", name: "P", scope: "phosphate", strategy: "direct", atoms: ["P"] },
    { beadID: "A2", name: "C4", scope: "sugar", strategy: "direct", atoms: ["C4'"] },
    { beadID: "A3", name: "N9", scope: "purine", strategy: "direct", atoms: ["N9"] },
    { beadID: "A3", name: "N1", scope: "pyrimidine", strategy: "direct", atoms: ["N1"] },
    { beadID: "A4", name: "C2", scope: "all", strategy: "direct", atoms: ["C2"] },
    { beadID: "A5", name: "C6", scope: "purine", strategy: "direct", atoms: ["C6"] },
    { beadID: "A5", name: "C4", scope: "pyrimidine", strategy: "direct", atoms: ["C4"] },
  ],
  intra_residues: [["A1", "A2"], ["A2", "A3"], ["A3", "A4"], ["A4", "A5"], ["A5", "A3"]],
  inter_residues: [{ source: "A5", target: "A1" }],
};

const UPLOAD_ENDPOINTS ={
  FILE: "/upload/file/",
  RCSB: "/upload/rcsb/",
  PRESET: "/upload/preset/",
}

const PRESETS = {
  1: "1EHZ",
  2: "1MNX",
  3: "2F8S",
}

JSON_MAX_CHARS = 5000;
JSON_MAX_UPLOAD_SIZE = 8 * 1024;
FILE_MAX_UPLOAD_SIZE = 100 * 1024 * 1024;
