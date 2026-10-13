import type { BeadMapping, ResidueMapping } from "@/api/types";

export interface MappingGroup {
  residueType: string;
  residues: string[];
  beads: readonly BeadMapping[];
}

export function groupMapping(mapping: readonly ResidueMapping[]): MappingGroup[] {
  const groupsByType = new Map<string, Map<string, MappingGroup>>();

  for (const { residue, residue_type: residueType, beads } of mapping) {
    let typeGroups = groupsByType.get(residueType);
    if (!typeGroups) {
      typeGroups = new Map();
      groupsByType.set(residueType, typeGroups);
    }

    const key = JSON.stringify(beads);
    const group = typeGroups.get(key);
    if (group) {
      group.residues.push(residue);
    } else {
      typeGroups.set(key, { residueType, residues: [residue], beads });
    }
  }

  return [...groupsByType.values()].flatMap((typeGroups) => [...typeGroups.values()]);
}
