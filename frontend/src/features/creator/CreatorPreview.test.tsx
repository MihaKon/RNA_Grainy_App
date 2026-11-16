import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { MolstarViewer } from "@/features/results/viewer/molstarViewer";

import CreatorPreview from "./CreatorPreview";
import { createDefaultDraft, draftReducer, type ModelDraft } from "./modelDraft";
import type * as PreviewStructure from "./previewStructure";
import type { PreviewResidue } from "./previewStructure";

const { createViewer, readStructure } = vi.hoisted(() => ({
  createViewer: vi.fn(),
  readStructure: vi.fn(),
}));
vi.mock("@/features/results/viewer/molstarViewer", () => ({
  createMolstarViewer: createViewer,
}));
vi.mock("./previewStructure", async (importOriginal) => ({
  ...(await importOriginal<typeof PreviewStructure>()),
  readPreviewSource: readStructure,
}));

const example: PreviewResidue[] = [
  {
    base: "A",
    chain: "A",
    sequence: 1,
    atoms: [
      { name: "P", element: "P", x: 1, y: 2, z: 3 },
      { name: "OP1", element: "O", x: 2, y: 4, z: 6 },
      { name: "C4'", element: "C", x: 3, y: 6, z: 9 },
      { name: "N9", element: "N", x: 4, y: 8, z: 12 },
      { name: "C2", element: "C", x: 5, y: 10, z: 15 },
      { name: "C6", element: "C", x: 6, y: 12, z: 18 },
    ],
  },
];

function fakeViewer() {
  return {
    failedStructures: [],
    hasNonPolymer: false,
    setVisibility: vi.fn(),
    setNonPolymerVisibility: vi.fn(),
    setRepresentation: vi.fn().mockResolvedValue(undefined),
    setColorMode: vi.fn().mockResolvedValue(undefined),
    replaceStructure: vi.fn().mockResolvedValue(undefined),
    dispose: vi.fn(),
  } satisfies MolstarViewer;
}

let viewer: ReturnType<typeof fakeViewer>;

function renderPreview(draft = createDefaultDraft()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const component = (model: ModelDraft, valid = true) => (
    <QueryClientProvider client={client}>
      <CreatorPreview draft={model} presetIds={["1EHZ"]} valid={valid} />
    </QueryClientProvider>
  );
  return { ...render(component(draft)), component, draft };
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("example")));
  viewer = fakeViewer();
  createViewer.mockReset().mockResolvedValue(viewer);
  readStructure.mockReset().mockResolvedValue({ residues: example });
});

describe("CreatorPreview", () => {
  it("shows input atoms, beads and reduction using the Results format", async () => {
    const app = renderPreview();
    expect(await screen.findByText("16.67%")).toBeInTheDocument();
    expect(screen.getByText("Input atoms (AA)").nextElementSibling).toHaveTextContent(
      "6",
    );
    expect(screen.getByText("CG beads").nextElementSibling).toHaveTextContent("5");
    const bead = app.draft.beads[0];
    if (!bead) throw new Error("Missing bead.");
    app.rerender(
      app.component(draftReducer(app.draft, { type: "removeBead", key: bead.key })),
    );
    expect(await screen.findByText("33.33%")).toBeInTheDocument();
    expect(screen.getByText("CG beads").nextElementSibling).toHaveTextContent("4");
  });
  it("updates only changed CG data and keeps one Molstar instance while editing", async () => {
    const app = renderPreview();
    await waitFor(() => {
      expect(createViewer).toHaveBeenCalledOnce();
    });
    const bead = app.draft.beads[0];
    if (!bead) throw new Error("Missing bead.");
    const changed = draftReducer(app.draft, {
      type: "toggleAtom",
      key: bead.key,
      atom: "OP1",
    });
    app.rerender(app.component(changed));
    await waitFor(() => {
      expect(viewer.replaceStructure).toHaveBeenCalledOnce();
    });
    expect(viewer.replaceStructure).toHaveBeenCalledWith(
      expect.objectContaining({ id: "coarse" }),
    );
    expect(createViewer).toHaveBeenCalledOnce();
    await userEvent.click(screen.getByRole("button", { name: "All-atom" }));
    expect(viewer.setVisibility).toHaveBeenCalledWith("reference", true);
  });

  it("keeps the last valid structure while a bead has no atoms", async () => {
    const app = renderPreview();
    await waitFor(() => {
      expect(createViewer).toHaveBeenCalledOnce();
    });
    app.rerender(app.component(draftReducer(app.draft, { type: "addBead" }), false));
    expect(screen.getByRole("status")).toHaveTextContent(
      "last valid model stays visible",
    );
    expect(viewer.dispose).not.toHaveBeenCalled();
    expect(viewer.replaceStructure).not.toHaveBeenCalled();
  });

  it("disposes a viewer that finishes initialization after closing the creator", async () => {
    let finish: (value: MolstarViewer) => void = () => undefined;
    createViewer.mockReturnValue(
      new Promise<MolstarViewer>((resolve) => {
        finish = resolve;
      }),
    );
    const app = renderPreview();
    await waitFor(() => {
      expect(createViewer).toHaveBeenCalledOnce();
    });
    app.unmount();
    finish(viewer);
    await waitFor(() => {
      expect(viewer.dispose).toHaveBeenCalledOnce();
    });
  });

  it("isolates a replacement still running when the selected base changes", async () => {
    const app = renderPreview();
    await waitFor(() => {
      expect(createViewer).toHaveBeenCalledOnce();
    });
    let finish: () => void = () => undefined;
    viewer.replaceStructure.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve;
        }),
    );
    const bead = app.draft.beads[0];
    if (!bead) throw new Error("Missing bead");
    app.rerender(
      app.component(
        draftReducer(app.draft, { type: "toggleAtom", key: bead.key, atom: "OP1" }),
      ),
    );
    await waitFor(() => {
      expect(viewer.replaceStructure).toHaveBeenCalledOnce();
    });
    const replacement = fakeViewer();
    createViewer.mockResolvedValue(replacement);
    await userEvent.selectOptions(screen.getByLabelText("Preview residues"), "A");
    await waitFor(() => {
      expect(createViewer).toHaveBeenCalledTimes(2);
    });
    finish();
    await waitFor(() => {
      expect(viewer.dispose).toHaveBeenCalledOnce();
    });
    expect(replacement.dispose).not.toHaveBeenCalled();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("hides stale geometry when no beads map to the selected RNA", async () => {
    const app = renderPreview();
    await waitFor(() => {
      expect(createViewer).toHaveBeenCalledOnce();
    });
    const bead = app.draft.beads[0];
    if (!bead) throw new Error("Missing bead");
    app.rerender(
      app.component({ ...app.draft, beads: [{ ...bead, scope: "uracil" }] }),
    );
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("No mapped atoms"),
    );
    expect(
      screen.getByLabelText("Molstar live preview").querySelector(".absolute.inset-0"),
    ).not.toBeVisible();
    app.rerender(app.component(app.draft));
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    expect(
      screen.getByLabelText("Molstar live preview").querySelector(".absolute.inset-0"),
    ).toBeVisible();
  });

  it("shows an error and lets the user reload an unavailable example", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(null, { status: 503 }))
        .mockResolvedValue(new Response("example")),
    );
    renderPreview();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not download the example",
    );
    await userEvent.click(screen.getByRole("button", { name: "Reload preview" }));
    await waitFor(() => {
      expect(createViewer).toHaveBeenCalledOnce();
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
