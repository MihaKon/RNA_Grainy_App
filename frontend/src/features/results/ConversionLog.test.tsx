import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { ConversionReport } from "@/api/types";

import { ConversionLog } from "./ConversionLog";

const report: ConversionReport = {
  created_beads: 5,
  skipped_beads: 5,
  skipped_residues: 1,
  estimated_atoms: 0,
  modified_residues: 1,
  residues: [
    {
      model: 1,
      chain: "1a",
      residue_id: "1533",
      residue_name: "PSU",
      canonical_name: "U",
      status: "skipped",
      missing_atoms: ["C4'", "N1"],
      estimated_atoms: [],
      created_beads: [],
      skipped_beads: ["P", "S", "B"],
      failures: { "C4'": "Insufficient reference atoms in the sugar ring." },
      ignored_altlocs: [],
      terminal_phosphate_absent: false,
    },
  ],
  skipped_connections: [
    {
      model: 1,
      chain: "1a",
      source_residue: "130",
      target_residue: "141",
      source_bead: "S",
      target_bead: "P",
      distance: 16.947,
    },
  ],
};

describe("ConversionLog", () => {
  it("explains absent reports for older results", () => {
    render(<ConversionLog report={undefined} filename="old" />);
    expect(screen.getByText(/not available for this result/)).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Download report" }),
    ).not.toBeInTheDocument();
  });

  it("shows backend diagnostics and skipped connection counts", () => {
    render(<ConversionLog report={report} filename="10PX" />);
    expect(screen.getByRole("region", { name: "Conversion report" })).toBeVisible();
    expect(screen.getByText("PSU 1533")).toBeVisible();
    expect(screen.getByText("Nucleotide skipped")).toBeVisible();
    expect(screen.getByText(/PSU → U/)).toBeVisible();
    expect(screen.getByText("Missing required atoms").parentElement).toHaveTextContent(
      "C4', N1",
    );
    expect(screen.getByText(/Insufficient reference atoms/)).toBeVisible();
    expect(screen.getByRole("table", { name: "Skipped connections" })).toBeVisible();
    expect(screen.getByText("16.95 Å")).toBeVisible();
    expect(
      screen.getByText("Skipped connections", { selector: "dt" }).parentElement,
    ).toHaveTextContent("1");
  });

  it("limits initial rendering of large reports and reveals more entries", async () => {
    const user = userEvent.setup();
    const entry = report.residues[0];
    if (!entry) throw new Error("Missing report fixture.");
    const largeReport = {
      ...report,
      residues: Array.from({ length: 51 }, (_, index) => ({
        ...entry,
        residue_id: String(index + 1),
      })),
      skipped_connections: [],
    };
    render(<ConversionLog report={largeReport} filename="large" />);
    expect(screen.queryByText("PSU 51")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show more entries" }));
    expect(screen.getByText("PSU 51")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Show more entries" }),
    ).not.toBeInTheDocument();
  });
});
