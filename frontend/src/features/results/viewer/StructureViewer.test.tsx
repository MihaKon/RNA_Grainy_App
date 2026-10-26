import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
    hasNonPolymer: false,
    setVisibility: vi.fn(),
    setNonPolymerVisibility: vi.fn(),
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

  it("keeps the CG model when the input structure cannot be loaded", async () => {
    const failedStructures: StructureId[] = ["reference"];
    createMolstarViewer.mockResolvedValue(fakeViewer({ failedStructures }));
    renderViewer();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The input structure could not be displayed.",
    );
    expect(screen.getByRole("button", { name: "CG model" })).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Input structure (all-atom)" }),
    ).toBeDisabled();
    expect(screen.getByRole("combobox", { name: "Color by" })).toBeDisabled();
    expect(screen.getByRole("combobox", { name: "Representation" })).toBeDisabled();
  });

  it("leaves multi-model navigation inside Molstar", async () => {
    createMolstarViewer.mockResolvedValue(fakeViewer());
    renderViewer();

    expect(
      await screen.findByRole("combobox", { name: "Representation" }),
    ).toBeEnabled();
    expect(screen.queryByRole("combobox", { name: "Model" })).not.toBeInTheDocument();
  });

  it("hides water, ions and ligands until they are switched on", async () => {
    const setNonPolymerVisibility = vi.fn();
    createMolstarViewer.mockResolvedValue(
      fakeViewer({ hasNonPolymer: true, setNonPolymerVisibility }),
    );
    const user = userEvent.setup();
    renderViewer();

    const toggle = await screen.findByRole("button", { name: "Water, ions & ligands" });
    expect(toggle).toHaveAttribute("aria-pressed", "false");

    await user.click(toggle);

    expect(setNonPolymerVisibility).toHaveBeenCalledWith(true);
    expect(toggle).toHaveAttribute("aria-pressed", "true");
  });

  it("offers no water and ligand switch for a structure without them", async () => {
    createMolstarViewer.mockResolvedValue(fakeViewer());
    renderViewer();

    expect(
      await screen.findByRole("combobox", { name: "Representation" }),
    ).toBeEnabled();
    expect(
      screen.queryByRole("button", { name: "Water, ions & ligands" }),
    ).not.toBeInTheDocument();
  });

  it("reports when neither structure can be displayed", async () => {
    createMolstarViewer.mockRejectedValue(
      new AggregateError([], "None of the structures could be loaded."),
    );
    renderViewer();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Neither structure could be displayed.",
    );
  });

  it("reports when the viewer itself cannot be started", async () => {
    createMolstarViewer.mockRejectedValue(new Error("WebGL is not available."));
    renderViewer();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The structure viewer could not be started.",
    );
  });
});
