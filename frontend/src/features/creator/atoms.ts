export const BEAD_SCOPES = [
  "all",
  "phosphate",
  "sugar",
  "purine",
  "pyrimidine",
  "adenine",
  "cytosine",
  "guanine",
  "uracil",
] as const;

export type BeadScope = (typeof BEAD_SCOPES)[number];

export const SCOPE_LABELS: Record<BeadScope, string> = {
  all: "All bases",
  phosphate: "Phosphate",
  sugar: "Sugar",
  purine: "Purines",
  pyrimidine: "Pyrimidines",
  adenine: "A",
  cytosine: "C",
  guanine: "G",
  uracil: "U",
};

export const ALL_RESIDUES = ["A", "G", "C", "U"] as const;

// Scopes without an entry apply to every residue through the default mapping.
export const SCOPE_RESIDUES: Partial<Record<BeadScope, readonly string[]>> = {
  purine: ["A", "G"],
  pyrimidine: ["C", "U"],
  adenine: ["A"],
  cytosine: ["C"],
  guanine: ["G"],
  uracil: ["U"],
};

export const SCOPE_ATOMS: Record<BeadScope, readonly string[]> = {
  all: ["N1", "C2", "N3", "C4", "C5", "C6", "N2"],
  phosphate: ["P", "OP1", "OP2"],
  sugar: ["C1'", "C2'", "C3'", "C4'", "C5'", "O2'", "O3'", "O4'", "O5'"],
  purine: ["N1", "C2", "N3", "C4", "C5", "C6", "N6", "N7", "C8", "N9", "N2", "O6"],
  pyrimidine: ["N1", "C2", "O2", "N3", "C4", "N4", "C5", "C6", "O4"],
  adenine: ["N1", "C2", "N3", "C4", "C5", "C6", "N6", "N7", "C8", "N9"],
  guanine: ["N1", "C2", "N2", "N3", "C4", "C5", "C6", "O6", "N7", "C8", "N9"],
  cytosine: ["N1", "C2", "O2", "N3", "C4", "N4", "C5", "C6"],
  uracil: ["N1", "C2", "O2", "N3", "C4", "O4", "C5", "C6"],
};

export const BEAD_STRATEGIES = [
  "direct",
  "center_of_mass",
  "geometric_center",
] as const;

export type BeadStrategy = (typeof BEAD_STRATEGIES)[number];

export const STRATEGY_LABELS: Record<BeadStrategy, string> = {
  direct: "Direct mapping",
  center_of_mass: "Center of mass",
  geometric_center: "Geometric center",
};

export function residuesForScope(scope: BeadScope): readonly string[] {
  return SCOPE_RESIDUES[scope] ?? ALL_RESIDUES;
}
