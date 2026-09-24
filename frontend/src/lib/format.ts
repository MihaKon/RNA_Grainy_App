const BYTE_UNITS = ["B", "KiB", "MiB", "GiB"] as const;

export function formatBytes(bytes: number): string {
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < BYTE_UNITS.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const rounded = Number.isInteger(value) ? value.toString() : value.toFixed(1);
  return `${rounded} ${BYTE_UNITS[unitIndex] ?? "B"}`;
}

export function formatList(items: readonly string[], conjunction = "or"): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} ${conjunction} ${items.at(-1) ?? ""}`;
}

export function formatBeadsPerResidue(beads: readonly number[]): string {
  const count = formatList(beads.map(String));
  const isSingular = beads.length === 1 && beads[0] === 1;
  return `${count} ${isSingular ? "bead" : "beads"} per residue`;
}

export function formatPercent(fraction: number): string {
  return `${(fraction * 100).toFixed(2)}%`;
}
