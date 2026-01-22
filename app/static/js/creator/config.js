const ATOM_DEFINITIONS = {
  all: [
    "N1",
    "C2",
    "O2",
    "N3",
    "C4",
    "N4",
    "C5",
    "C6",
    "O4",
    "N6",
    "N7",
    "C8",
    "N9",
    "N2",
    "O6",
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
