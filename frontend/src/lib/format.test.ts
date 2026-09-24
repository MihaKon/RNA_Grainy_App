import { describe, expect, it } from "vitest";

import {
  formatBeadCount,
  formatBeadsPerResidue,
  formatBytes,
  formatList,
  formatPercent,
} from "./format";

describe("format", () => {
  it.each([
    [512, "512 B"],
    [8 * 1024, "8 KiB"],
    [1.5 * 1024 ** 2, "1.5 MiB"],
    [100 * 1024 ** 2, "100 MiB"],
  ])("formats %d bytes as %s", (bytes, expected) => {
    expect(formatBytes(bytes)).toBe(expected);
  });

  it("joins lists with a conjunction", () => {
    expect(formatList(["pdb"])).toBe("pdb");
    expect(formatList(["pdb", "cif", "mmcif"])).toBe("pdb, cif or mmcif");
    expect(formatList(["a", "b"], "and")).toBe("a and b");
  });

  it("describes bead counts", () => {
    expect(formatBeadCount([2, 3])).toBe("2 or 3");
    expect(formatBeadsPerResidue([1])).toBe("1 bead per residue");
    expect(formatBeadsPerResidue([6, 7])).toBe("6 or 7 beads per residue");
  });

  it("formats fractions as percentages", () => {
    expect(formatPercent(0.8298)).toBe("82.98%");
  });
});
