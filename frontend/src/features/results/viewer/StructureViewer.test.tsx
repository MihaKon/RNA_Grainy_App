import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ResultStructures } from "@/api/results";

import type { MolstarViewer, StructureId } from "./molstarViewer";
import { StructureViewer } from "./StructureViewer";

const createMolstarViewer = vi.hoisted(() => vi.fn());
vi.mock("./molstarViewer", () => ({ createMolstarViewer }));

const structures: ResultStructures = {
  reference: "reference",
  coarseMmcif: "coarse mmcif",
  coarsePdb: "coarse pdb",
  coarsePdbFailed: false,
};

function fakeViewer(overrides: Partial<MolstarViewer> = {}): MolstarViewer {
  return {
    failedStructures: [],
    setVisibility: vi.fn(),
    setRepresentation: vi.fn(() => Promise.resolve()),
    setColorMode: vi.fn(() => Promise.resolve()),
    dispose: vi.fn(),
    ...overrides,
  };
}

function renderViewer() {
  return render(<StructureViewer structures={structures} referenceFormat="mmcif" />);
}

describe("StructureViewer", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  it("keeps the coarse-grained structure when the all-atom one cannot be loaded", async () => {
    const failedStructures: StructureId[] = ["reference"];
    createMolstarViewer.mockResolvedValue(fakeViewer({ failedStructures }));
    renderViewer();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The all-atom structure could not be displayed.",
    );
    expect(screen.getByRole("button", { name: "Coarse-grained" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "All-atom" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "By element" })).toBeDisabled();
  });

  it("reports that the viewer failed only when no structure can be loaded", async () => {
    createMolstarViewer.mockRejectedValue(new Error("Unreadable files."));
    renderViewer();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The structure viewer could not be started.",
    );
  });
});
