import { type BeadDraft, type ModelDraft, uniqueBeadIds } from "./modelDraft";

export const BEAD_COLORS = [
  "#d89425",
  "#5b9b72",
  "#0091c9",
  "#8874ae",
  "#cf7186",
  "#439c9e",
  "#687ac6",
];

export function beadColor(draft: ModelDraft, bead: BeadDraft): string {
  return (
    BEAD_COLORS[uniqueBeadIds(draft).indexOf(bead.beadId) % BEAD_COLORS.length] ??
    "#0091c9"
  );
}
