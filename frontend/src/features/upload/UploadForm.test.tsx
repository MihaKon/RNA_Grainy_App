import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { appConfig, coarseGrainResult, models } from "@/test/fixtures";
import { jsonResponse, mockFetch, requestBody } from "@/test/fetchMock";
import { renderApp } from "@/test/renderApp";

const catalogRoutes = {
  "GET /api/config": () => jsonResponse(appConfig),
  "GET /api/models": () => jsonResponse(models),
};

async function renderForm() {
  const app = renderApp("/");
  await screen.findByRole("button", { name: "Coarse-grain structure" });
  return app;
}

describe("UploadForm", () => {
  beforeEach(() => {
    mockFetch(catalogRoutes);
  });

  it("lists models alphabetically followed by the custom option", async () => {
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

    expect(await screen.findByText("Model report")).toBeInTheDocument();
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

    await screen.findByText("Model report");
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

    await screen.findByText("Model report");
    const body = requestBody(fetchMock, "/api/coarse-grain/rcsb");
    expect(body.get("rcsb_id")).toBe("1EHZ");
    expect(body.get("selected_model")).toBe("custom");
    expect(body.get("custom_model_data")).toBe(definition);
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
