import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { jsonResponse, mockFetch, requestBody } from "@/test/fetchMock";
import { appConfig, coarseGrainResult, models } from "@/test/fixtures";
import { renderApp } from "@/test/renderApp";

import { createDefaultDraft, serializeDefinition, toDefinition } from "./modelDraft";

function mockApi() {
  return mockFetch({
    "GET /api/config": () => jsonResponse(appConfig),
    "GET /api/models": () => jsonResponse(models),
    "POST /api/models/custom/validate": () => new Response(null, { status: 204 }),
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

    await user.click(screen.getByRole("tab", { name: "Use example" }));
    await user.click(screen.getByRole("radio", { name: "1EHZ" }));
    await user.click(screen.getByRole("button", { name: "Submit" }));

    await screen.findByText("Conversion summary");
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

  it("removes invalid imported connections", async () => {
    const { user, dialog } = await openCreator();
    const imported = {
      ...toDefinition(createDefaultDraft()),
      connectivity: { intra_residue: [["A1", "B9"]], inter_residue: [] },
    };

    await user.upload(
      within(dialog).getByLabelText("Import model JSON file"),
      new File([JSON.stringify(imported)], "imported.json"),
    );
    const issue = await within(dialog).findByText(
      "Connection A1–B9 uses undefined bead B9.",
    );
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeDisabled();

    await user.click(
      within(dialog).getByRole("button", {
        name: "Remove invalid connections",
      }),
    );
    expect(issue).not.toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeEnabled();
  });

  it("blocks a model that exceeds the byte size limit", async () => {
    const { user, dialog } = await openCreator();

    await user.click(within(dialog).getByLabelText("Model name"));
    await user.paste("€".repeat(2500));

    expect(
      within(dialog).getByText("The model definition exceeds the 8 KiB limit."),
    ).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeDisabled();
    expect(within(dialog).getByRole("button", { name: "Export JSON" })).toBeDisabled();
  });

  it("keeps editing when Enter is pressed in a creator field", async () => {
    const { user } = renderApp("/");
    await user.click(await screen.findByRole("tab", { name: "Use example" }));
    await user.click(screen.getByRole("radio", { name: "1EHZ" }));
    await user.selectOptions(screen.getByLabelText("Coarse-grained model"), "custom");
    await user.click(screen.getByRole("button", { name: "Open creator" }));
    await user.click(screen.getByRole("button", { name: "Use model" }));
    await user.click(screen.getByRole("button", { name: "Edit" }));
    const dialog = screen.getByRole("dialog", { name: "Model creator" });

    await user.type(within(dialog).getByLabelText("Model name"), " v2{Enter}");

    expect(screen.getByRole("dialog", { name: "Model creator" })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalledWith(
      "/api/coarse-grain/preset",
      expect.anything(),
    );
  });

  it("shows imported atoms that the scope does not offer", async () => {
    const { user, dialog } = await openCreator();
    const imported = toDefinition(createDefaultDraft());
    imported.default_mapping.config.atom_centers.A1 = ["P", "O1P"];
    imported.default_mapping.config.strategies.A1 = "center_of_mass";

    await user.upload(
      within(dialog).getByLabelText("Import model JSON file"),
      new File([serializeDefinition(imported)], "imported.json"),
    );

    const bead = await within(dialog).findByRole("article", { name: "Bead A1" });
    const extraAtom = within(bead).getByRole("button", { name: "O1P" });
    expect(extraAtom).toHaveAttribute("aria-pressed", "true");

    await user.click(extraAtom);
    expect(within(bead).queryByRole("button", { name: "O1P" })).not.toBeInTheDocument();
  });

  it("explains why a loaded model cannot be edited", async () => {
    const { user } = renderApp("/");
    await user.selectOptions(
      await screen.findByLabelText("Coarse-grained model"),
      "custom",
    );
    const definition = toDefinition(createDefaultDraft());
    definition.default_mapping.residues.push("PSU");
    await user.upload(
      screen.getByLabelText("Custom model JSON file"),
      new File([serializeDefinition(definition)], "modified.json"),
    );

    await user.click(await screen.findByRole("button", { name: "Edit" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(
      screen.getByText("The creator supports residues A, G, C and U, not PSU."),
    ).toBeInTheDocument();
  });

  it("starts from scratch and reloads the SimRNA template", async () => {
    const { user, dialog } = await openCreator();
    const nameField = within(dialog).getByRole("textbox", { name: "Model name" });

    await user.click(
      within(dialog).getByRole("button", { name: "Start from scratch" }),
    );
    expect(nameField).toHaveValue("");
    expect(
      within(dialog)
        .getAllByRole("article")
        .map((bead) => bead.ariaLabel),
    ).toEqual(["Bead A1"]);
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeDisabled();

    await user.click(
      within(dialog).getByRole("button", { name: "Load SimRNA template" }),
    );
    expect(nameField).toHaveValue("Custom Model");
    expect(within(dialog).getAllByRole("article")).toHaveLength(7);
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeEnabled();
  });
});
