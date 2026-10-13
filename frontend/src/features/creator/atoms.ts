export const ALL_RESIDUES = ["A", "G", "C", "U"] as const;

type Residue = (typeof ALL_RESIDUES)[number];

const BASE_ATOMS: Record<Residue, readonly string[]> = {
  A: ["N1", "C2", "N3", "C4", "C5", "C6", "N6", "N7", "C8", "N9"],
  G: ["N1", "C2", "N2", "N3", "C4", "C5", "C6", "O6", "N7", "C8", "N9"],
  C: ["N1", "C2", "O2", "N3", "C4", "N4", "C5", "C6"],
  U: ["N1", "C2", "O2", "N3", "C4", "O4", "C5", "C6"],
};

interface ScopeDefinition {
  label: string;
  // Scopes without residues apply to every residue through the default mapping.
  residues?: readonly Residue[];
  atoms: readonly string[];
}

function baseScope(label: string, residues: readonly Residue[]): ScopeDefinition {
  const atoms = new Set(residues.flatMap((residue) => BASE_ATOMS[residue]));
  return { label, residues, atoms: [...atoms] };
}

const SCOPE_DEFINITIONS = {
  all: { label: "All bases", atoms: ["N1", "C2", "N3", "C4", "C5", "C6", "N2"] },
  phosphate: { label: "Phosphate", atoms: ["P", "OP1", "OP2"] },
  sugar: {
    label: "Sugar",
    atoms: ["C1'", "C2'", "C3'", "C4'", "C5'", "O2'", "O3'", "O4'", "O5'"],
  },
  purine: baseScope("Purines", ["A", "G"]),
  pyrimidine: baseScope("Pyrimidines", ["C", "U"]),
  adenine: baseScope("A", ["A"]),
  cytosine: baseScope("C", ["C"]),
  guanine: baseScope("G", ["G"]),
  uracil: baseScope("U", ["U"]),
} satisfies Record<string, ScopeDefinition>;

export type BeadScope = keyof typeof SCOPE_DEFINITIONS;

export const SCOPES: Record<BeadScope, ScopeDefinition> = SCOPE_DEFINITIONS;

export const BEAD_SCOPES = Object.keys(SCOPES) as BeadScope[];

export const STRATEGY_LABELS = {
  direct: "Direct mapping",
  center_of_mass: "Center of mass",
  geometric_center: "Geometric center",
};

export type BeadStrategy = keyof typeof STRATEGY_LABELS;

export const BEAD_STRATEGIES = Object.keys(STRATEGY_LABELS) as BeadStrategy[];

export function residuesForScope(scope: BeadScope): readonly string[] {
  return SCOPES[scope].residues ?? ALL_RESIDUES;
}
