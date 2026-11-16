import { type Residue, SCOPES } from "./atoms";
import type { BeadDraft } from "./modelDraft";

export type Point = readonly [number, number];

const BACKBONE: Record<string, Point> = {
  P: [43, 110],
  OP1: [14.716, 81.716],
  OP2: [14.716, 138.284],
  "O5'": [83, 110],
  "C5'": [117.641, 130],
  "C4'": [117.641, 170],
  "O4'": [150.002, 146.489],
  "C1'": [182.362, 170],
  "C2'": [170.002, 208.042],
  "C3'": [130.002, 208.042],
  "O2'": [182.362, 246.085],
  "O3'": [106.49, 240.403],
};
const PYRIMIDINE: Record<string, Point> = {
  N1: [222.362, 170],
  C2: [222.362, 130],
  N3: [257.003, 110],
  C4: [291.644, 130],
  C5: [291.644, 170],
  C6: [257.003, 190],
  O2: [187.721, 110],
};
const PURINE: Record<string, Point> = {
  N9: [221.958, 157.361],
  C8: [198.446, 125],
  N7: [221.958, 92.639],
  C5: [260, 105],
  C4: [260, 145],
  N3: [294.641, 165],
  C2: [329.282, 145],
  N1: [329.282, 105],
  C6: [294.641, 85],
};
const BACKBONE_BONDS = [
  ["P", "OP1"],
  ["P", "OP2"],
  ["P", "O5'"],
  ["O5'", "C5'"],
  ["C5'", "C4'"],
  ["C4'", "O4'"],
  ["O4'", "C1'"],
  ["C1'", "C2'"],
  ["C2'", "C3'"],
  ["C3'", "C4'"],
  ["C2'", "O2'"],
  ["C3'", "O3'"],
] as const;

export function nucleotideDiagram(residue: Residue) {
  const purine = residue === "A" || residue === "G";
  const atoms: Record<string, Point> = {
    ...BACKBONE,
    ...(purine ? PURINE : PYRIMIDINE),
  };
  const ring = purine
    ? ["N9", "C8", "N7", "C5", "C4", "N9", "C1'"]
    : ["N1", "C2", "N3", "C4", "C5", "C6", "N1", "C1'"];
  const bonds: (readonly [string, string])[] = [...BACKBONE_BONDS];
  ring.forEach((atom, i) => {
    const previous = ring[i - 1];
    if (previous) bonds.push([previous, atom]);
  });
  if (purine) {
    const second = ["C5", "C6", "N1", "C2", "N3", "C4"];
    second.forEach((atom, i) => {
      const previous = second[i - 1];
      if (previous) bonds.push([previous, atom]);
    });
  } else bonds.push(["C2", "O2"]);
  const branch =
    residue === "A"
      ? (["C6", "N6", 294.641, 45] as const)
      : residue === "G"
        ? (["C6", "O6", 294.641, 45] as const)
        : residue === "C"
          ? (["C4", "N4", 326.285, 110] as const)
          : (["C4", "O4", 326.285, 110] as const);
  atoms[branch[1]] = [branch[2], branch[3]];
  bonds.push([branch[0], branch[1]]);
  if (residue === "G") {
    atoms.N2 = [363.923, 165];
    bonds.push(["C2", "N2"]);
  }
  return { atoms, bonds };
}

export function beadPoint(bead: BeadDraft, atoms: Record<string, Point>): Point | null {
  const selected = bead.atoms.flatMap((name) =>
    atoms[name] ? [{ name, point: atoms[name] }] : [],
  );
  if (selected.length === 0) return null;
  const weights = selected.map(({ name }) =>
    bead.strategy === "center_of_mass" ? atomicMass(name[0] ?? "C") : 1,
  );
  const total = weights.reduce((a, b) => a + b, 0);
  const coordinate = (axis: 0 | 1) =>
    selected.reduce((sum, atom, i) => sum + atom.point[axis] * (weights[i] ?? 1), 0) /
    total;
  return [coordinate(0), coordinate(1)];
}

export function atomicMass(element: string): number {
  return (
    (
      { C: 12.011, N: 14.007, O: 15.999, P: 30.974, H: 1.008 } as Record<string, number>
    )[element.toUpperCase()] ?? 12.011
  );
}

export function beadLabels(beads: BeadDraft[], atoms: Record<string, Point>) {
  const markers = beads.flatMap((bead) => {
    const point = beadPoint(bead, atoms);
    return point ? [{ bead, point, label: [8, 32] as Point }] : [];
  });
  const atomBounds = Object.entries(atoms).map(([name, [x, y]]) => ({
    x: x - Math.max(15, (name.length * 7 + 4) / 2) - 4,
    y: y - 17,
    width: Math.max(30, name.length * 7 + 4) + 8,
    height: 34,
  }));
  const overlap = (
    x: number,
    y: number,
    other: { x: number; y: number; width: number; height: number },
  ) =>
    Math.max(0, Math.min(x + 40, other.x + other.width) - Math.max(x - 4, other.x)) *
    Math.max(0, Math.min(y + 24, other.y + other.height) - Math.max(y - 4, other.y));
  const candidates = markers.map(({ point }) => {
    const positions: Point[] = [];
    const add = (x: number, y: number) =>
      positions.push([Math.max(8, Math.min(346, x)), Math.max(32, Math.min(246, y))]);
    for (const radius of [38, 52, 70, 92, 120]) {
      for (let direction = 0; direction < 24; direction++) {
        const angle = (direction * Math.PI) / 12;
        add(
          point[0] + Math.cos(angle) * radius - 18,
          point[1] + Math.sin(angle) * radius - 10,
        );
      }
    }
    for (let y = 32; y <= 246; y += 14) {
      for (let x = 8; x <= 346; x += 18) add(x, y);
    }
    return positions;
  });
  const placed = new Set<number>();
  for (let pass = 0; pass < 4; pass++) {
    markers.forEach((marker, index) => {
      const score = ([x, y]: Point) => {
        const atomOverlap = atomBounds.reduce(
          (sum, bounds) => sum + overlap(x, y, bounds),
          0,
        );
        const labelOverlap = markers.reduce(
          (sum, other, otherIndex) =>
            otherIndex !== index && placed.has(otherIndex)
              ? sum +
                overlap(x, y, {
                  x: other.label[0] - 4,
                  y: other.label[1] - 4,
                  width: 44,
                  height: 28,
                })
              : sum,
          0,
        );
        const beadOverlap = markers.reduce((sum, other) => {
          const dx = Math.max(x - other.point[0], 0, other.point[0] - x - 36);
          const dy = Math.max(y - other.point[1], 0, other.point[1] - y - 20);
          return sum + Math.max(0, 21 - Math.hypot(dx, dy));
        }, 0);
        return (
          labelOverlap * 100000 +
          atomOverlap * 10000 +
          beadOverlap * 10000 +
          Math.hypot(x + 18 - marker.point[0], y + 10 - marker.point[1])
        );
      };
      let bestScore = Infinity;
      for (const position of candidates[index] ?? []) {
        const value = score(position);
        if (value < bestScore) {
          bestScore = value;
          marker.label = position;
        }
      }
      placed.add(index);
    });
  }
  return markers;
}

export function isDoubleBond(residue: Residue, a: string, b: string) {
  const pairs =
    residue === "A"
      ? ["C6:N1", "C2:N3", "C4:C5", "N7:C8"]
      : residue === "G"
        ? ["C6:O6", "C2:N3", "C4:C5", "N7:C8"]
        : residue === "C"
          ? ["C2:O2", "N3:C4", "C5:C6"]
          : ["C2:O2", "C4:O4", "C5:C6"];
  return pairs.includes(`${a}:${b}`) || pairs.includes(`${b}:${a}`);
}

export function availableDiagramAtom(bead: BeadDraft, atom: string) {
  return SCOPES[bead.scope].atoms.includes(atom) || bead.atoms.includes(atom);
}
