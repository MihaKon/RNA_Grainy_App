import { BEAD_SCOPES, BEAD_STRATEGIES } from "./atoms";
import {
  type BeadDraft,
  createBead,
  isRecord,
  isStringPair,
  type ModelDraft,
} from "./modelDraft";

const STORAGE_KEY = "rnagrainy.creator-draft.v1";

export interface StoredCreatorDraft {
  source: string | null;
  draft: ModelDraft;
}

export function readCreatorDraft(): StoredCreatorDraft | null {
  try {
    const stored: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "null");
    if (
      !isRecord(stored) ||
      !(stored.source === null || typeof stored.source === "string") ||
      !isRecord(stored.draft)
    )
      return null;
    const draft = stored.draft;
    if (
      typeof draft.name !== "string" ||
      typeof draft.description !== "string" ||
      !Array.isArray(draft.beads) ||
      !draft.beads.every(
        (bead): bead is BeadDraft =>
          isRecord(bead) &&
          ["key", "beadId", "name", "description"].every(
            (field) => typeof bead[field] === "string",
          ) &&
          BEAD_SCOPES.some((scope) => scope === bead.scope) &&
          BEAD_STRATEGIES.some((strategy) => strategy === bead.strategy) &&
          Array.isArray(bead.atoms) &&
          bead.atoms.every((atom) => typeof atom === "string"),
      ) ||
      !Array.isArray(draft.intraResidue) ||
      !draft.intraResidue.every(isStringPair) ||
      !isRecord(draft.interResidue) ||
      !(
        draft.interResidue.source === null ||
        typeof draft.interResidue.source === "string"
      ) ||
      !(
        draft.interResidue.target === null ||
        typeof draft.interResidue.target === "string"
      )
    )
      return null;
    return {
      source: stored.source,
      draft: {
        name: draft.name,
        description: draft.description,
        beads: draft.beads.map(({ key, ...bead }) => createBead(bead)),
        intraResidue: draft.intraResidue,
        interResidue: {
          source: draft.interResidue.source,
          target: draft.interResidue.target,
        },
      },
    };
  } catch {
    return null;
  }
}

export function writeCreatorDraft(stored: StoredCreatorDraft): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  } catch {
    return;
  }
}
