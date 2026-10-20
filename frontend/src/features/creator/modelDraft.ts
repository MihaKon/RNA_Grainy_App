import { CustomModelFileError } from "@/features/upload/customModel";

import {
  ALL_RESIDUES,
  BEAD_SCOPES,
  BEAD_STRATEGIES,
  type BeadScope,
  type BeadStrategy,
  type Residue,
  residuesForScope,
  residuesWithoutAtom,
  SCOPES,
} from "./atoms";

export interface BeadDraft {
  key: string;
  beadId: string;
  name: string;
  scope: BeadScope;
  strategy: BeadStrategy;
  description: string;
  atoms: string[];
}

export interface InterResidueDraft {
  source: string | null;
  target: string | null;
}

export interface ModelDraft {
  name: string;
  description: string;
  beads: BeadDraft[];
  intraResidue: [string, string][];
  interResidue: InterResidueDraft;
}

interface MappingConfig {
  bead_names: Record<string, string>;
  atom_centers: Record<string, string[]>;
  description: Record<string, string>;
  strategies: Record<string, string>;
}

interface MappingEntry {
  residues: string[];
  config: MappingConfig;
}

// Mirrors CustomModelDefinition in app/models/custom_model.py.
export interface CustomModelDefinition {
  model_name: string;
  description: string;
  default_mapping: MappingEntry;
  mapping: MappingEntry[];
  connectivity: {
    intra_residue: [string, string][];
    inter_residue: { source: string; target: string }[];
  };
}

export type DraftAction =
  | { type: "replace"; draft: ModelDraft }
  | { type: "setModelInfo"; patch: Partial<Pick<ModelDraft, "name" | "description">> }
  | { type: "addBead" }
  | { type: "removeBead"; key: string }
  | {
      type: "updateBead";
      key: string;
      patch: Partial<Pick<BeadDraft, "name" | "description">>;
    }
  | { type: "renameBead"; key: string; beadId: string }
  | { type: "setBeadScope"; key: string; scope: BeadScope }
  | { type: "setBeadStrategy"; key: string; strategy: BeadStrategy }
  | { type: "toggleAtom"; key: string; atom: string }
  | { type: "toggleIntraConnection"; first: string; second: string }
  | { type: "setInterConnection"; end: keyof InterResidueDraft; beadId: string }
  | { type: "clearInterConnection" }
  | { type: "removeInvalidConnections" };

let beadKeyCounter = 0;

function createBead(bead: Omit<BeadDraft, "key">): BeadDraft {
  beadKeyCounter += 1;
  return { key: `bead-${beadKeyCounter.toString()}`, ...bead };
}

export function createDefaultDraft(): ModelDraft {
  const direct = (beadId: string, name: string, scope: BeadScope, atom: string) =>
    createBead({
      beadId,
      name,
      scope,
      strategy: "direct",
      description: "",
      atoms: [atom],
    });

  return {
    name: "Custom Model",
    description: "Custom Model based on SimRNA.",
    beads: [
      direct("A1", "P", "phosphate", "P"),
      direct("A2", "C4'", "sugar", "C4'"),
      direct("A3", "N9", "purine", "N9"),
      direct("A3", "N1", "pyrimidine", "N1"),
      direct("A4", "C2", "all", "C2"),
      direct("A5", "C6", "purine", "C6"),
      direct("A5", "C4", "pyrimidine", "C4"),
    ],
    intraResidue: [
      ["A1", "A2"],
      ["A2", "A3"],
      ["A3", "A4"],
      ["A4", "A5"],
      ["A5", "A3"],
    ],
    interResidue: { source: "A2", target: "A1" },
  };
}

export function uniqueBeadIds(draft: ModelDraft): string[] {
  return [...new Set(draft.beads.map((bead) => bead.beadId))];
}

export function hasIntraConnection(draft: ModelDraft, first: string, second: string) {
  return draft.intraResidue.some(
    ([a, b]) => (a === first && b === second) || (a === second && b === first),
  );
}

// Imported definitions can connect bead IDs that no bead defines.
function isDefinedBead(draft: ModelDraft): (beadId: string | null) => boolean {
  const beadIds = new Set(uniqueBeadIds(draft));
  return (beadId) => beadId === null || beadIds.has(beadId);
}

// The connectivity matrix cannot show these, so they only come from imports.
function intraConnectionIssues(draft: ModelDraft): (string | null)[] {
  const isDefined = isDefinedBead(draft);
  return draft.intraResidue.map(([a, b], index) => {
    const label = `Connection ${a}–${b}`;
    const missing = [...new Set([a, b])].filter((beadId) => !isDefined(beadId));
    if (missing.length > 0)
      return `${label} uses undefined bead ${missing.join(", ")}.`;
    if (a === b) return `${label} connects a bead to itself.`;
    const first = draft.intraResidue.findIndex(
      ([c, d]) => (c === a && d === b) || (c === b && d === a),
    );
    return first === index ? null : `${label} is listed twice.`;
  });
}

export function draftReducer(draft: ModelDraft, action: DraftAction): ModelDraft {
  switch (action.type) {
    case "replace":
      return action.draft;

    case "setModelInfo":
      return { ...draft, ...action.patch };

    case "addBead": {
      const usedIds = new Set(draft.beads.map((bead) => bead.beadId));
      let index = draft.beads.length + 1;
      while (usedIds.has(`A${index.toString()}`)) index += 1;
      const beadId = `A${index.toString()}`;
      return {
        ...draft,
        beads: [
          ...draft.beads,
          createBead({
            beadId,
            name: beadId,
            scope: "all",
            strategy: "direct",
            description: "",
            atoms: [],
          }),
        ],
      };
    }

    case "removeBead": {
      const removed = draft.beads.find((bead) => bead.key === action.key);
      const beads = draft.beads.filter((bead) => bead.key !== action.key);
      const next = { ...draft, beads };
      const idStillUsed = beads.some((bead) => bead.beadId === removed?.beadId);
      return removed && !idStillUsed ? removeConnections(next, removed.beadId) : next;
    }

    case "updateBead":
      return updateBead(draft, action.key, (bead) => ({ ...bead, ...action.patch }));

    case "renameBead": {
      const bead = draft.beads.find((candidate) => candidate.key === action.key);
      if (!bead) return draft;
      const next = updateBead(draft, action.key, (current) => ({
        ...current,
        beadId: action.beadId,
      }));
      const oldIdStillUsed = next.beads.some(
        (candidate) => candidate.beadId === bead.beadId,
      );
      return oldIdStillUsed
        ? next
        : renameConnections(next, bead.beadId, action.beadId);
    }

    case "setBeadScope":
      return updateBead(draft, action.key, (bead) => ({
        ...bead,
        scope: action.scope,
        atoms: [],
      }));

    case "setBeadStrategy":
      return updateBead(draft, action.key, (bead) => ({
        ...bead,
        strategy: action.strategy,
        atoms: action.strategy === "direct" ? bead.atoms.slice(0, 1) : bead.atoms,
      }));

    case "toggleAtom":
      return updateBead(draft, action.key, (bead) => {
        if (bead.atoms.includes(action.atom)) {
          return { ...bead, atoms: bead.atoms.filter((atom) => atom !== action.atom) };
        }
        return {
          ...bead,
          atoms:
            bead.strategy === "direct" ? [action.atom] : [...bead.atoms, action.atom],
        };
      });

    case "toggleIntraConnection": {
      const { first, second } = action;
      if (first === second) return draft;
      return {
        ...draft,
        intraResidue: hasIntraConnection(draft, first, second)
          ? draft.intraResidue.filter(
              ([a, b]) =>
                !((a === first && b === second) || (a === second && b === first)),
            )
          : [...draft.intraResidue, [first, second]],
      };
    }

    case "setInterConnection":
      return {
        ...draft,
        interResidue: { ...draft.interResidue, [action.end]: action.beadId },
      };

    case "clearInterConnection":
      return { ...draft, interResidue: { source: null, target: null } };

    case "removeInvalidConnections": {
      const intraIssues = intraConnectionIssues(draft);
      const isDefined = isDefinedBead(draft);
      const { source, target } = draft.interResidue;
      return {
        ...draft,
        intraResidue: draft.intraResidue.filter(
          (_, index) => intraIssues[index] === null,
        ),
        interResidue:
          isDefined(source) && isDefined(target)
            ? draft.interResidue
            : { source: null, target: null },
      };
    }
  }
}

function updateBead(
  draft: ModelDraft,
  key: string,
  update: (bead: BeadDraft) => BeadDraft,
): ModelDraft {
  return {
    ...draft,
    beads: draft.beads.map((bead) => (bead.key === key ? update(bead) : bead)),
  };
}

function removeConnections(draft: ModelDraft, beadId: string): ModelDraft {
  const { source, target } = draft.interResidue;
  return {
    ...draft,
    intraResidue: draft.intraResidue.filter((pair) => !pair.includes(beadId)),
    interResidue:
      source === beadId || target === beadId
        ? { source: null, target: null }
        : draft.interResidue,
  };
}

function renameConnections(draft: ModelDraft, from: string, to: string): ModelDraft {
  const rename = (beadId: string | null) => (beadId === from ? to : beadId);
  return {
    ...draft,
    intraResidue: draft.intraResidue.map(([a, b]) => [rename(a) ?? a, rename(b) ?? b]),
    interResidue: {
      source: rename(draft.interResidue.source),
      target: rename(draft.interResidue.target),
    },
  };
}

export interface DraftIssues {
  beads: Record<string, string[]>;
  model: string[];
  invalidConnections: boolean;
}

export function validateDraft(draft: ModelDraft): DraftIssues {
  const issues: DraftIssues = { beads: {}, model: [], invalidConnections: false };
  const beadsByResidue = new Map<string, string>();
  const namesByResidue = new Map<string, string>();

  if (!draft.name.trim()) issues.model.push("Enter a model name.");
  if (draft.beads.length === 0) issues.model.push("Add at least one bead.");

  for (const bead of draft.beads) {
    const beadIssues: string[] = [];
    if (!bead.beadId.trim()) beadIssues.push("Enter a bead ID.");
    if (!bead.name.trim()) beadIssues.push("Enter a bead name.");
    if (bead.atoms.length === 0) beadIssues.push("Select at least one atom.");
    if (bead.strategy === "direct" && bead.atoms.length > 1) {
      beadIssues.push("Direct mapping uses exactly one atom.");
    }

    for (const atom of bead.atoms) {
      const missing = residuesWithoutAtom(atom, residuesForScope(bead.scope));
      if (missing.length > 0) {
        beadIssues.push(`${atom} is missing from ${missing.join(", ")}.`);
      }
    }

    const conflicts = residuesForScope(bead.scope).filter(
      (residue) => beadsByResidue.get(`${bead.beadId}:${residue}`) !== undefined,
    );
    if (bead.beadId.trim() && conflicts.length > 0) {
      beadIssues.push(
        `Bead ${bead.beadId} is already defined for ${conflicts.join(", ")}.`,
      );
    }
    for (const residue of residuesForScope(bead.scope)) {
      beadsByResidue.set(`${bead.beadId}:${residue}`, bead.key);
    }

    // The backend looks atoms up by name, so a residue needs unique bead names.
    const nameConflicts = residuesForScope(bead.scope).filter((residue) =>
      namesByResidue.has(`${bead.name}:${residue}`),
    );
    if (bead.name.trim() && nameConflicts.length > 0) {
      beadIssues.push(
        `Bead name ${bead.name} is already used for ${nameConflicts.join(", ")}.`,
      );
    }
    for (const residue of residuesForScope(bead.scope)) {
      namesByResidue.set(`${bead.name}:${residue}`, bead.key);
    }

    if (beadIssues.length > 0) issues.beads[bead.key] = beadIssues;
  }

  const { source, target } = draft.interResidue;
  if ((source === null) !== (target === null)) {
    issues.model.push("Choose both beads of the inter-residue connection.");
  }

  const intraIssues = intraConnectionIssues(draft).filter((issue) => issue !== null);
  const isDefined = isDefinedBead(draft);
  const missingInter = [source, target].filter((beadId) => !isDefined(beadId));
  issues.model.push(...intraIssues);
  if (missingInter.length > 0) {
    issues.model.push(
      `Inter-residue connection ${source ?? "?"} → ${target ?? "?"} uses undefined bead ${missingInter.join(", ")}.`,
    );
  }
  issues.invalidConnections = intraIssues.length > 0 || missingInter.length > 0;

  return issues;
}

const emptyConfig = (): MappingConfig => ({
  bead_names: {},
  atom_centers: {},
  description: {},
  strategies: {},
});

export function toDefinition(draft: ModelDraft): CustomModelDefinition {
  const defaultMapping: MappingEntry = {
    residues: [...ALL_RESIDUES],
    config: emptyConfig(),
  };
  const mappings = new Map<BeadScope, MappingEntry>();

  for (const bead of draft.beads) {
    const residues = SCOPES[bead.scope].residues;
    let entry = defaultMapping;
    if (residues) {
      entry = mappings.get(bead.scope) ?? {
        residues: [...residues],
        config: emptyConfig(),
      };
      mappings.set(bead.scope, entry);
    }

    entry.config.bead_names[bead.beadId] = bead.name;
    entry.config.atom_centers[bead.beadId] = bead.atoms;
    entry.config.description[bead.beadId] = bead.description;
    entry.config.strategies[bead.beadId] = bead.strategy;
  }

  const { source, target } = draft.interResidue;
  return {
    model_name: draft.name,
    description: draft.description,
    default_mapping: defaultMapping,
    mapping: [...mappings.values()],
    connectivity: {
      intra_residue: draft.intraResidue,
      inter_residue: source && target ? [{ source, target }] : [],
    },
  };
}

export function serializeDefinition(definition: CustomModelDefinition): string {
  return JSON.stringify(definition, null, 2);
}

interface ResolvedBead {
  name: string;
  atoms: string[];
  strategy: BeadStrategy;
  description: string;
}

// Mirrors _build_nucleotide_config() in app/coarse_grain/models.py: each residue starts
// from the default mapping, and every mapping entry for it overrides single keys.
export function resolveBeads(
  definition: Record<string, unknown>,
): Map<Residue, Map<string, ResolvedBead>> {
  const configs = new Map<Residue, Record<string, Record<string, unknown>>>();
  const apply = (entry: unknown) => {
    if (!isRecord(entry) || !isRecord(entry.config)) return;
    for (const residue of entryResidues(entry)) {
      const config = configs.get(residue) ?? {};
      for (const [field, values] of Object.entries(entry.config)) {
        if (isRecord(values)) config[field] = { ...config[field], ...values };
      }
      configs.set(residue, config);
    }
  };
  apply(definition.default_mapping);
  if (Array.isArray(definition.mapping)) definition.mapping.forEach(apply);

  const resolved = new Map<Residue, Map<string, ResolvedBead>>();
  for (const [residue, config] of configs) {
    const atomCenters = config.atom_centers ?? {};
    const descriptions = stringRecord(config.description);
    const strategies = stringRecord(config.strategies);
    const beads = new Map<string, ResolvedBead>();
    for (const [beadId, name] of Object.entries(stringRecord(config.bead_names))) {
      const strategy = strategies[beadId];
      beads.set(beadId, {
        name,
        atoms: stringList(atomCenters[beadId]),
        strategy: isStrategy(strategy) ? strategy : "direct",
        description: descriptions[beadId] ?? "",
      });
    }
    resolved.set(residue, beads);
  }
  return resolved;
}

function entryResidues(entry: Record<string, unknown>): Residue[] {
  return stringList(entry.residues).map((name) => {
    const residue = ALL_RESIDUES.find((candidate) => candidate === name.toUpperCase());
    if (!residue) {
      throw new CustomModelFileError(
        `The creator supports residues A, G, C and U, not ${name}.`,
      );
    }
    return residue;
  });
}

export function fromDefinition(definition: Record<string, unknown>): ModelDraft {
  const resolved = resolveBeads(definition);

  // Residues that define a bead identically share one bead in the creator.
  const groups = new Map<
    string,
    { beadId: string; bead: ResolvedBead; residues: Residue[] }
  >();
  for (const residue of ALL_RESIDUES) {
    for (const [beadId, bead] of resolved.get(residue) ?? []) {
      const key = JSON.stringify([beadId, bead]);
      const group = groups.get(key) ?? { beadId, bead, residues: [] };
      group.residues.push(residue);
      groups.set(key, group);
    }
  }

  const beads = [...groups.values()].flatMap(({ beadId, bead, residues }) => {
    const scope = scopeForResidues(residues, bead.atoms);
    if (scope) return [createBead({ beadId, ...bead, scope })];
    return residues.map((residue) =>
      createBead({ beadId, ...bead, scope: BASE_SCOPES[residue] }),
    );
  });

  const connectivity = isRecord(definition.connectivity) ? definition.connectivity : {};
  const intraResidue = Array.isArray(connectivity.intra_residue)
    ? connectivity.intra_residue.filter(isStringPair)
    : [];
  const interLink =
    Array.isArray(connectivity.inter_residue) && isRecord(connectivity.inter_residue[0])
      ? connectivity.inter_residue[0]
      : {};

  return {
    name:
      typeof definition.model_name === "string"
        ? definition.model_name
        : "Imported Model",
    description:
      typeof definition.description === "string" ? definition.description : "",
    beads,
    intraResidue,
    interResidue: {
      source: typeof interLink.source === "string" ? interLink.source : null,
      target: typeof interLink.target === "string" ? interLink.target : null,
    },
  };
}

const BASE_SCOPES: Record<Residue, BeadScope> = {
  A: "adenine",
  G: "guanine",
  C: "cytosine",
  U: "uracil",
};

function scopeForResidues(
  residues: readonly Residue[],
  atoms: readonly string[],
): BeadScope | undefined {
  if (residues.length === ALL_RESIDUES.length) {
    // All, phosphate and sugar beads cover every residue; pick the one offering most atoms.
    const overlap = (scope: BeadScope) =>
      atoms.filter((atom) => SCOPES[scope].atoms.includes(atom)).length;
    return BEAD_SCOPES.filter((scope) => !SCOPES[scope].residues).reduce(
      (best, scope) => (overlap(scope) > overlap(best) ? scope : best),
    );
  }
  const key = [...residues].sort().join();
  return BEAD_SCOPES.find(
    (scope) =>
      SCOPES[scope].residues && [...residuesForScope(scope)].sort().join() === key,
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item) => typeof item === "string") : [];
}

function stringRecord(value: unknown): Record<string, string> {
  if (!isRecord(value)) return {};
  return Object.fromEntries(
    Object.entries(value).filter(
      (entry): entry is [string, string] => typeof entry[1] === "string",
    ),
  );
}

function isStrategy(value: unknown): value is BeadStrategy {
  return BEAD_STRATEGIES.some((strategy) => strategy === value);
}

function isStringPair(value: unknown): value is [string, string] {
  return (
    Array.isArray(value) &&
    value.length === 2 &&
    value.every((item) => typeof item === "string")
  );
}
