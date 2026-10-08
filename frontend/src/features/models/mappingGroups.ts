import type { BeadMapping, ResidueMapping } from "@/api/types";

export interface MappingGroup {
  residueType: string;
  residues: string[];
  beads: readonly BeadMapping[];
}

export function groupMapping(mapping: readonly ResidueMapping[]): MappingGroup[] {
  const groups: MappingGroup[] = [];
  const groupsByKey = new Map<string, MappingGroup>();

  for (const { residue, residue_type: residueType, beads } of mapping) {
    const key = JSON.stringify([residueType, beads]);
    const group = groupsByKey.get(key);
    if (group) {
      group.residues.push(residue);
    } else {
      const newGroup = { residueType, residues: [residue], beads };
      groupsByKey.set(key, newGroup);
      groups.push(newGroup);
    }
  }

  return groups.sort(
    (a, b) =>
      groups.findIndex((group) => group.residueType === a.residueType) -
      groups.findIndex((group) => group.residueType === b.residueType),
  );
}
