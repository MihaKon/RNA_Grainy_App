import type { StructureId } from "./molstarViewer";

// Deliberately outside the RNAPolis palette: these colors were tuned with researchers
// for contrast against Mol*'s white background and against each other.
export const STRUCTURE_COLORS: Record<StructureId, number> = {
  reference: 0x047857,
  coarse: 0xf97316,
};
