import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { appConfig, coarseGrainResult, models } from "@/test/fixtures";
import { jsonResponse, mockFetch, requestBody } from "@/test/fetchMock";
import { renderApp } from "@/test/renderApp";

import { createDefaultDraft, serializeDefinition, toDefinition } from "./modelDraft";

function mockApi() {
  return mockFetch({
    "GET /api/config": () => jsonResponse(appConfig),
    "GET /api/models": () => jsonResponse(models),
    "POST /api/coarse-grain/preset": () => jsonResponse(coarseGrainResult),
  });
}

async function openCreator() {
  const app = renderApp("/");
  const { user } = app;
  await user.selectOptions(
    await screen.findByLabelText("Coarse-grained model"),
    "custom",
  );
  await user.click(screen.getByRole("button", { name: "Open creator" }));
  return { ...app, dialog: screen.getByRole("dialog", { name: "Model creator" }) };
}

describe("ModelCreator", () => {
  let fetchMock: ReturnType<typeof mockApi>;

  beforeEach(() => {
    fetchMock = mockApi();
  });

  it("applies the default model and submits its definition", async () => {
    const { user, dialog } = await openCreator();

    await user.click(within(dialog).getByRole("button", { name: "Use model" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText("Custom model loaded")).toBeInTheDocument();
    expect(screen.getByText("Model creator")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Example" }));
    await user.click(screen.getByRole("radio", { name: "1EHZ" }));
    await user.click(screen.getByRole("button", { name: "Coarse-grain structure" }));

    await screen.findByText("Model report");
    expect(
      requestBody(fetchMock, "/api/coarse-grain/preset").get("custom_model_data"),
    ).toBe(serializeDefinition(toDefinition(createDefaultDraft())));
  });

  it("blocks the model until every bead has atoms", async () => {
    const { user, dialog } = await openCreator();
    const useModel = within(dialog).getByRole("button", { name: "Use model" });

    await user.click(within(dialog).getByRole("button", { name: "Add bead" }));

    const newBead = within(dialog).getByRole("article", { name: "Bead A8" });
    expect(within(newBead).getByText("Select at least one atom.")).toBeInTheDocument();
    expect(useModel).toBeDisabled();

    await user.click(within(newBead).getByRole("button", { name: "Phosphate" }));
    await user.click(within(newBead).getByRole("button", { name: "P" }));
    expect(useModel).toBeEnabled();
  });

  it("keeps connections in sync with the beads", async () => {
    const { user, dialog } = await openCreator();

    await user.click(within(dialog).getByRole("tab", { name: "Connectivity" }));
    const link = within(dialog).getByRole("button", { name: "Connect A1 and A2" });
    expect(link).toHaveAttribute("aria-pressed", "true");

    await user.click(link);
    expect(link).toHaveAttribute("aria-pressed", "false");
    expect(
      within(dialog).getByText(/"intra_residue": \[\s*\[\s*"A2"/),
    ).toBeInTheDocument();
  });

  it("edits a model loaded from JSON and discards changes on cancel", async () => {
    const app = renderApp("/");
    const { user } = app;
    await user.selectOptions(
      await screen.findByLabelText("Coarse-grained model"),
      "custom",
    );
    await user.upload(
      screen.getByLabelText("Custom model JSON file"),
      new File(
        [
          serializeDefinition({
            ...toDefinition(createDefaultDraft()),
            model_name: "Loaded",
          }),
        ],
        "loaded.json",
      ),
    );
    await screen.findByText("Loaded");

    await user.click(screen.getByRole("button", { name: "Edit" }));
    const dialog = screen.getByRole("dialog", { name: "Model creator" });
    const nameField = within(dialog).getByRole("textbox", { name: "Model name" });
    expect(nameField).toHaveValue("Loaded");

    await user.clear(nameField);
    await user.type(nameField, "Changed");
    await user.click(within(dialog).getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText("Loaded")).toBeInTheDocument();
    expect(screen.getByText("loaded.json")).toBeInTheDocument();
  });

  it("imports a definition into the creator", async () => {
    const { user, dialog } = await openCreator();
    const imported = { ...toDefinition(createDefaultDraft()), model_name: "Imported" };

    await user.upload(
      within(dialog).getByLabelText("Import model JSON file"),
      new File([serializeDefinition(imported)], "imported.json"),
    );

    expect(await within(dialog).findByDisplayValue("Imported")).toBeInTheDocument();
  });
});
