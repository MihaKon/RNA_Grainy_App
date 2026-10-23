import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createDefaultDraft, toDefinition } from "@/features/creator/modelDraft";
import { jsonResponse, mockFetch, requestBody } from "@/test/fetchMock";
import { appConfig, coarseGrainResult, models } from "@/test/fixtures";
import { renderApp } from "@/test/renderApp";

const catalogRoutes = {
  "GET /api/config": () => jsonResponse(appConfig),
  "GET /api/models": () => jsonResponse(models),
  "POST /api/models/custom/validate": () => new Response(null, { status: 204 }),
};

const coarseGrainRoutes = {
  ...catalogRoutes,
  "POST /api/coarse-grain/file": () => jsonResponse(coarseGrainResult),
  "POST /api/coarse-grain/rcsb": () => jsonResponse(coarseGrainResult),
  "POST /api/coarse-grain/preset": () => jsonResponse(coarseGrainResult),
};

type SourceKind = "file" | "rcsb" | "preset";
type User = Awaited<ReturnType<typeof renderForm>>["user"];

const structureFile = new File(["ATOM"], "1EHZ.pdb");

const SOURCE_FIELDS: Record<SourceKind, string> = {
  file: "file",
  rcsb: "rcsb_id",
  preset: "preset_id",
};

const EXPECTED_SOURCE_VALUES: Record<SourceKind, File | string> = {
  file: structureFile,
  rcsb: "1EHZ",
  preset: "1MNX",
};

async function fillSource(user: User, kind: SourceKind) {
  switch (kind) {
    case "file":
      await user.click(screen.getByRole("tab", { name: "Upload file" }));
      await user.upload(screen.getByLabelText(/choose a file/i), structureFile);
      break;
    case "rcsb":
      await user.click(screen.getByRole("tab", { name: "PDB ID" }));
      await user.type(screen.getByRole("textbox", { name: "PDB ID" }), "1ehz");
      break;
    case "preset":
      await user.click(screen.getByRole("tab", { name: "Example" }));
      await user.click(screen.getByRole("radio", { name: "1MNX" }));
      break;
  }
}

async function loadCustomModel(user: User, definition: string) {
  await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "custom");
  await user.upload(
    screen.getByLabelText("Custom model JSON file"),
    new File([definition], "model.json", { type: "application/json" }),
  );
  await screen.findByText("Two-bead model");
}

async function renderForm() {
  const app = renderApp("/");
  await screen.findByRole("button", { name: "Coarse-grain structure" });
  return app;
}

describe("UploadForm", () => {
  it("lists models alphabetically followed by the custom option", async () => {
    mockFetch({
      ...catalogRoutes,
      "GET /api/models": () => jsonResponse(models.toReversed()),
    });
    await renderForm();

    const options = within(screen.getByLabelText("Coarse-grained model"))
      .getAllByRole("option")
      .map((option) => option.textContent);
    expect(options).toEqual([
      "Select a model",
      "NAST",
      "SimRNA",
      "Custom model (JSON)",
    ]);
  });

  it("shows validation errors instead of submitting an incomplete form", async () => {
    const fetchMock = mockFetch(catalogRoutes);
    const { user } = await renderForm();

    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    expect(screen.getByText("Choose a structure file.")).toBeInTheDocument();
    expect(screen.getByText("Select a coarse-grained model.")).toBeInTheDocument();
    expect(screen.getByLabelText("Coarse-grained model")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/coarse-grain"),
      expect.anything(),
    );
  });

  it("processes an example structure and opens the result", async () => {
    const fetchMock = mockFetch({
      ...catalogRoutes,
      "POST /api/coarse-grain/preset": () => jsonResponse(coarseGrainResult),
    });
    const { router, user } = await renderForm();

    await user.click(screen.getByRole("tab", { name: "Example" }));
    await user.click(screen.getByRole("radio", { name: "1EHZ" }));
    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "SimModel");
    await user.type(screen.getByLabelText("Chains"), "A");
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    expect(await screen.findByText("Conversion summary")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe(
      `/results/${coarseGrainResult.workspace_id}`,
    );
    const body = requestBody(fetchMock, "/api/coarse-grain/preset");
    expect(body.get("preset_id")).toBe("1EHZ");
    expect(body.get("selected_model")).toBe("SimModel");
    expect(body.get("chains")).toBe("A");
  });

  it("uploads a structure file", async () => {
    const fetchMock = mockFetch({
      ...catalogRoutes,
      "POST /api/coarse-grain/file": () => jsonResponse(coarseGrainResult),
    });
    const { user } = await renderForm();
    const file = new File(["ATOM"], "1EHZ.pdb");

    await user.upload(screen.getByLabelText(/choose a file/i), file);
    expect(screen.getByText("1EHZ.pdb")).toBeInTheDocument();
    await user.selectOptions(
      screen.getByLabelText("Coarse-grained model"),
      "NASTModel",
    );
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    await screen.findByText("Conversion summary");
    expect(requestBody(fetchMock, "/api/coarse-grain/file").get("file")).toEqual(file);
  });

  it("sends a loaded custom model definition", async () => {
    const fetchMock = mockFetch({
      ...catalogRoutes,
      "POST /api/coarse-grain/rcsb": () => jsonResponse(coarseGrainResult),
    });
    const { user } = await renderForm();
    const definition = JSON.stringify({ model_name: "Two-bead model" });

    await user.click(screen.getByRole("tab", { name: "PDB ID" }));
    await user.type(screen.getByRole("textbox", { name: "PDB ID" }), "1ehz");
    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "custom");
    await user.upload(
      screen.getByLabelText("Custom model JSON file"),
      new File([definition], "model.json", { type: "application/json" }),
    );
    expect(await screen.findByText("Two-bead model")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    await screen.findByText("Conversion summary");
    const body = requestBody(fetchMock, "/api/coarse-grain/rcsb");
    expect(body.get("rcsb_id")).toBe("1EHZ");
    expect(body.get("selected_model")).toBe("custom");
    expect(body.get("custom_model_data")).toBe(definition);
  });

  it.each<[SourceKind, SourceKind]>([
    ["file", "preset"],
    ["preset", "file"],
    ["rcsb", "file"],
    ["file", "rcsb"],
  ])("sends only the new source after switching from %s to %s", async (first, last) => {
    const fetchMock = mockFetch(coarseGrainRoutes);
    const { user } = await renderForm();

    await fillSource(user, first);
    await fillSource(user, last);
    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "SimModel");
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    await screen.findByText("Conversion summary");
    const urls = fetchMock.mock.calls.map(([input]) => input);
    expect(urls).not.toContain(`/api/coarse-grain/${first}`);
    const body = requestBody(fetchMock, `/api/coarse-grain/${last}`);
    expect(body.get(SOURCE_FIELDS[last])).toEqual(EXPECTED_SOURCE_VALUES[last]);
    expect(body.has(SOURCE_FIELDS[first])).toBe(false);
  });

  it("drops a loaded custom model after switching to a published one", async () => {
    const fetchMock = mockFetch(coarseGrainRoutes);
    const { user } = await renderForm();

    await fillSource(user, "preset");
    await loadCustomModel(user, JSON.stringify({ model_name: "Two-bead model" }));
    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "SimModel");
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    await screen.findByText("Conversion summary");
    const body = requestBody(fetchMock, "/api/coarse-grain/preset");
    expect(body.get("selected_model")).toBe("SimModel");
    expect(body.has("custom_model_data")).toBe(false);
  });

  it("sends a custom model loaded after a published one was selected", async () => {
    const fetchMock = mockFetch(coarseGrainRoutes);
    const { user } = await renderForm();
    const definition = JSON.stringify({ model_name: "Two-bead model" });

    await fillSource(user, "preset");
    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "SimModel");
    await loadCustomModel(user, definition);
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    await screen.findByText("Conversion summary");
    const body = requestBody(fetchMock, "/api/coarse-grain/preset");
    expect(body.get("selected_model")).toBe("custom");
    expect(body.get("custom_model_data")).toBe(definition);
  });

  it("lets the same file be chosen again after a reset", async () => {
    const fetchMock = mockFetch(coarseGrainRoutes);
    const { user } = await renderForm();
    const fileInput = screen.getByLabelText<HTMLInputElement>(/choose a file/i);

    await user.upload(fileInput, structureFile);
    expect(fileInput.value).not.toBe("");
    await user.click(screen.getByRole("button", { name: "Reset" }));

    expect(fileInput.value).toBe("");
    await user.upload(fileInput, structureFile);
    expect(screen.getByText("1EHZ.pdb")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "SimModel");
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));
    await screen.findByText("Conversion summary");
    expect(requestBody(fetchMock, "/api/coarse-grain/file").get("file")).toEqual(
      structureFile,
    );
  });

  it("does not load a custom model the server rejects", async () => {
    mockFetch({
      ...catalogRoutes,
      "POST /api/models/custom/validate": () =>
        jsonResponse(
          { detail: "Invalid custom model: default_mapping: Field required" },
          422,
        ),
    });
    const { user } = await renderForm();

    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "custom");
    await user.upload(
      screen.getByLabelText("Custom model JSON file"),
      new File(['{"model_name": "Broken"}'], "model.json", {
        type: "application/json",
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid custom model: default_mapping: Field required",
    );
    expect(screen.queryByText("Custom model loaded")).not.toBeInTheDocument();
  });

  it("opens a rejected custom model in the creator to fix it", async () => {
    mockFetch({
      ...catalogRoutes,
      "POST /api/models/custom/validate": () =>
        jsonResponse(
          {
            detail:
              "Invalid custom model: Connection A1–B9: bead B9 is not defined for A, G, C, U.",
          },
          422,
        ),
    });
    const { user } = await renderForm();
    const definition = {
      ...toDefinition(createDefaultDraft()),
      model_name: "Broken",
      connectivity: { intra_residue: [["A1", "B9"]], inter_residue: [] },
    };

    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "custom");
    await user.upload(
      screen.getByLabelText("Custom model JSON file"),
      new File([JSON.stringify(definition)], "broken.json"),
    );
    await user.click(await screen.findByRole("button", { name: "Fix in creator" }));

    const dialog = screen.getByRole("dialog", { name: "Model creator" });
    expect(within(dialog).getByRole("textbox", { name: "Model name" })).toHaveValue(
      "Broken",
    );
    await user.click(
      within(dialog).getByRole("button", { name: "Remove invalid connections" }),
    );
    await user.click(within(dialog).getByRole("button", { name: "Use model" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText("Custom model loaded")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows the server error message", async () => {
    mockFetch({
      ...catalogRoutes,
      "POST /api/coarse-grain/rcsb": () =>
        jsonResponse({ detail: "Could not fetch file for RCSB ID: 9XYZ" }, 422),
    });
    const { user } = await renderForm();

    await user.click(screen.getByRole("tab", { name: "PDB ID" }));
    await user.type(screen.getByRole("textbox", { name: "PDB ID" }), "9xyz");
    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "SimModel");
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not fetch file for RCSB ID: 9XYZ",
    );
    expect(
      screen.getByRole("button", { name: "Coarse-grain structure" }),
    ).toBeEnabled();
  });

  it("offers a retry when the models cannot be loaded", async () => {
    mockFetch({
      "GET /api/config": () => jsonResponse(appConfig),
      "GET /api/models": () => jsonResponse({ detail: "Server error" }, 500),
    });
    renderApp("/");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not load the available models.",
    );
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });
});
