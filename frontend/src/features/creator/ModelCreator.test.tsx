import { fireEvent, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { jsonResponse, mockFetch, requestBody } from "@/test/fetchMock";
import { appConfig, coarseGrainResult, models } from "@/test/fixtures";
import { renderApp } from "@/test/renderApp";

import { createDefaultDraft, serializeDefinition, toDefinition } from "./modelDraft";

vi.mock("./CreatorPreview", () => ({ default: () => <div>Live preview</div> }));

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
  await user.click(await screen.findByRole("button", { name: "Custom model" }));
  await user.click(screen.getByRole("button", { name: "Open creator" }));
  return { ...app, dialog: screen.getByRole("dialog", { name: "Model creator" }) };
}

async function openModelMenu(
  user: ReturnType<typeof renderApp>["user"],
  dialog: HTMLElement,
) {
  const control = within(dialog).getByLabelText("Model actions menu");
  if (!control.parentElement?.hasAttribute("open")) await user.click(control);
}

async function openModelDetails(
  user: ReturnType<typeof renderApp>["user"],
  dialog: HTMLElement,
) {
  const control = within(dialog).getByLabelText("Model details");
  if (!control.parentElement?.hasAttribute("open")) await user.click(control);
}

async function openBeadSettings(
  user: ReturnType<typeof renderApp>["user"],
  dialog: HTMLElement,
) {
  if (!within(dialog).queryByRole("region", { name: "Bead settings" }))
    await user.click(within(dialog).getByRole("button", { name: "Bead settings" }));
}

describe("ModelCreator", () => {
  it.each(["Model details", "Model actions menu"])(
    "handles focus changes safely in %s",
    async (label) => {
      const { user, dialog } = await openCreator();
      const control = within(dialog).getByLabelText(label);
      const dropdown = control.closest("details");
      await user.click(control);
      expect(dropdown).toHaveAttribute("open");
      fireEvent.focusOut(control, { relatedTarget: control });
      expect(dropdown).toHaveAttribute("open");
      const windowBlur = new FocusEvent("focusout", { bubbles: true });
      Object.defineProperty(windowBlur, "relatedTarget", { value: window });
      fireEvent(control, windowBlur);
      expect(dropdown).not.toHaveAttribute("open");
      expect(dialog).toBeInTheDocument();
      await user.click(control);
      fireEvent.focusOut(control, { relatedTarget: null });
      expect(dropdown).not.toHaveAttribute("open");
      await user.click(control);
      await user.click(within(dialog).getByRole("button", { name: "Map atoms" }));
      expect(dropdown).not.toHaveAttribute("open");
    },
  );
  let fetchMock: ReturnType<typeof mockApi>;

  beforeEach(() => {
    fetchMock = mockApi();
  });

  it("removes beads from the selector and settings and updates connectivity", async () => {
    const { user, dialog } = await openCreator();
    await user.click(within(dialog).getByLabelText("Select bead"));
    await user.click(
      within(dialog).getByRole("menuitem", {
        name: "Remove bead A1 (P, Phosphate) from list",
      }),
    );
    expect(
      within(dialog).queryByRole("menuitemradio", { name: /A1/ }),
    ).not.toBeInTheDocument();
    expect(
      within(dialog).queryByRole("region", { name: "Bead settings" }),
    ).not.toBeInTheDocument();
    await openBeadSettings(user, dialog);
    expect(
      within(dialog).getByRole("article", { name: "Bead A2" }),
    ).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "Remove bead A2" }));
    expect(
      within(dialog).getByRole("article", { name: "Bead A3" }),
    ).toBeInTheDocument();
    await user.click(
      within(dialog).getByRole("button", { name: "Close bead settings" }),
    );
    await user.click(within(dialog).getByRole("button", { name: "JSON preview" }));
    const json = dialog.querySelector("pre");
    expect(json).toHaveTextContent('"inter_residue": []');
    expect(json).not.toHaveTextContent('"A1"');
    expect(json).not.toHaveTextContent('"A2"');
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeEnabled();
  });

  it("selects beads independently of opening their settings", async () => {
    const { user, dialog } = await openCreator();
    const selector = within(dialog).getByLabelText("Select bead");
    await user.click(selector);
    await user.click(
      within(dialog).getByRole("menuitemradio", { name: /A3.*N9.*Purines/ }),
    );
    expect(
      within(dialog).queryByRole("region", { name: "Bead settings" }),
    ).not.toBeInTheDocument();
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead A2 C4'" }),
    );
    expect(
      within(dialog).getByRole("status", { name: "Active bead summary" }),
    ).toHaveTextContent("A2");
    expect(
      within(dialog).queryByRole("region", { name: "Bead settings" }),
    ).not.toBeInTheDocument();
    await openBeadSettings(user, dialog);
    expect(
      within(dialog).getByRole("article", { name: "Bead A2" }),
    ).toBeInTheDocument();
  });

  it("switches the selected bead without closing its settings", async () => {
    const { user, dialog } = await openCreator();
    const control = within(dialog).getByRole("button", { name: "Bead settings" });
    expect(control).toHaveAttribute("aria-expanded", "false");
    await user.click(control);
    const settings = within(dialog).getByRole("region", { name: "Bead settings" });
    expect(within(settings).queryByLabelText("Selected bead")).not.toBeInTheDocument();
    const selector = within(dialog).getByLabelText("Select bead");
    await user.click(selector);
    await user.click(
      within(dialog).getByRole("menuitemradio", { name: /A3.*N9.*Purines/ }),
    );
    expect(selector).toHaveFocus();
    expect(within(settings).getByLabelText("Bead ID")).toHaveValue("A3");
    expect(
      within(dialog).getByRole("status", { name: "Active bead summary" }),
    ).toHaveTextContent("A3");
    expect(control).toHaveAttribute("aria-expanded", "true");
    await user.click(control);
    expect(
      within(dialog).queryByRole("region", { name: "Bead settings" }),
    ).not.toBeInTheDocument();
  });

  it("starts with two views and opens settings only when requested", async () => {
    const { user, dialog } = await openCreator();
    expect(
      within(dialog).queryByRole("region", { name: "Bead settings" }),
    ).not.toBeInTheDocument();
    expect(within(dialog).getByLabelText("Model name")).not.toBeVisible();
    expect(
      within(dialog).getByText("Export model as JSON", { selector: "button" }),
    ).not.toBeVisible();
    await user.click(within(dialog).getByRole("button", { name: "Bead settings" }));
    const settings = within(dialog).getByRole("region", { name: "Bead settings" });
    expect(settings).toHaveFocus();
    await user.click(within(settings).getByRole("button", { name: "OP1" }));
    await user.keyboard("{Escape}");
    expect(
      within(dialog).queryByRole("region", { name: "Bead settings" }),
    ).not.toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Bead settings" })).toHaveFocus();
    expect(within(dialog).getByRole("button", { name: "A atom OP1" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(dialog).toBeInTheDocument();
    await openModelDetails(user, dialog);
    expect(within(dialog).getByRole("textbox", { name: "Model name" })).toBeVisible();
    await openModelMenu(user, dialog);
    expect(within(dialog).getByLabelText("Model name")).not.toBeVisible();
    expect(
      within(dialog).getByRole("button", { name: "Export model as JSON" }),
    ).toBeVisible();
  });

  it("chooses the strategy when adding a bead and exposes its atom list immediately", async () => {
    const { user, dialog } = await openCreator();
    await user.click(within(dialog).getByRole("button", { name: "Add bead" }));
    await user.click(within(dialog).getByRole("menuitem", { name: "Center of mass" }));
    const bead = within(within(dialog).getByRole("article", { name: "Bead A8" }));
    expect(bead.getByLabelText("Strategy")).toHaveValue("center_of_mass");
    expect(bead.getByRole("button", { name: "P" })).toBeInTheDocument();
    expect(bead.getByRole("button", { name: "C4'" })).toBeInTheDocument();
    expect(
      within(dialog).getByRole("status", { name: "Active bead summary" }),
    ).toHaveTextContent("A8");
    await user.click(bead.getByRole("button", { name: "P" }));
    await user.click(bead.getByRole("button", { name: "OP1" }));
    expect(within(dialog).getByRole("button", { name: "A atom OP1" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("offers a compatible scope for base-specific atoms and highlights editable bases", async () => {
    const { user, dialog } = await openCreator();
    await openModelMenu(user, dialog);
    await user.click(
      within(dialog).getByRole("button", { name: "Start from scratch" }),
    );
    await openBeadSettings(user, dialog);
    await user.selectOptions(
      within(within(dialog).getByRole("article", { name: "Bead A1" })).getByLabelText(
        "Strategy",
      ),
      "center_of_mass",
    );
    await user.click(
      within(within(dialog).getByRole("article", { name: "Bead A1" })).getByRole(
        "button",
        { name: "P" },
      ),
    );
    await user.click(within(dialog).getByRole("button", { name: "A atom N9" }));
    await user.click(
      within(dialog).getByRole("button", { name: "Use Purines and select N9" }),
    );
    expect(within(dialog).getByRole("button", { name: "A atom N9" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(within(dialog).getByRole("button", { name: "A atom P" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(within(dialog).getByRole("button", { name: "G atom N9" })).toHaveAttribute(
      "aria-disabled",
      "false",
    );
    expect(within(dialog).getByRole("button", { name: "C atom N1" })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    expect(
      within(dialog).getByLabelText("Uracil atom diagram").parentElement,
    ).toHaveAttribute("data-editable", "false");
  });

  it("creates and removes an inter-residue connection on the 2D editor", async () => {
    const { user, dialog } = await openCreator();
    await user.click(within(dialog).getByRole("button", { name: "Connect beads" }));
    expect(
      within(dialog).getByRole("button", { name: "Connect beads" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(within(dialog).getByRole("button", { name: "Map atoms" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    await user.selectOptions(within(dialog).getByLabelText("Connection type"), "inter");
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead A1 P" }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead A2 C4'" }),
    );
    await user.click(within(dialog).getByRole("button", { name: "JSON preview" }));
    const json = dialog.querySelector("pre");
    expect(json).toHaveTextContent('"source": "A1"');
    expect(json).toHaveTextContent('"target": "A2"');
    await user.click(
      within(dialog).getByRole("button", {
        name: "Remove 2D inter-residue connection",
      }),
    );
    expect(json).toHaveTextContent('"inter_residue": []');
    await user.click(within(dialog).getByRole("button", { name: "Map atoms" }));
    expect(within(dialog).queryByLabelText("Connection type")).not.toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "Connect beads" }));
    expect(within(dialog).getByLabelText("Connection type")).toHaveValue("inter");
    expect(
      within(dialog).getByRole("button", { name: "Live preview" }),
    ).toBeInTheDocument();
  });

  it("shows all four bases and keeps every mapping scope in the bead settings", async () => {
    const { user, dialog } = await openCreator();
    expect(dialog.querySelectorAll("svg[aria-label$='atom diagram']")).toHaveLength(4);
    expect(
      within(dialog).queryByRole("group", { name: "Visible bases" }),
    ).not.toBeInTheDocument();
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead A3 N9" }),
    );
    await openBeadSettings(user, dialog);
    const bead = within(within(dialog).getByRole("article", { name: "Bead A3" }));
    for (const label of ["All bases", "A", "C", "G", "U", "Purines", "Pyrimidines"])
      expect(bead.getByRole("button", { name: label })).toBeInTheDocument();
    expect(bead.getByRole("button", { name: "Purines" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(bead.getByRole("button", { name: "N9" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(
      within(dialog).getByRole("status", { name: "Active bead summary" }),
    ).toHaveTextContent("A3");
    expect(
      within(dialog).getByLabelText("Adenine atom diagram").parentElement,
    ).toHaveAttribute("data-editable", "true");
    expect(
      within(dialog).getByLabelText("Cytosine atom diagram").parentElement,
    ).toHaveAttribute("data-editable", "false");
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
    await user.click(within(dialog).getByRole("menuitem", { name: "Direct mapping" }));

    const newBead = within(dialog).getByRole("article", { name: "Bead A8" });
    expect(within(newBead).getByText("Select at least one atom.")).toBeInTheDocument();
    expect(useModel).toBeDisabled();

    await user.click(within(newBead).getByRole("button", { name: "Phosphate" }));
    expect(within(newBead).getByRole("button", { name: "P" })).toBeDisabled();
    expect(within(dialog).getByRole("button", { name: "A atom P" })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    await user.click(within(dialog).getByRole("button", { name: "A atom P" }));
    expect(useModel).toBeDisabled();
    expect(within(dialog).getByRole("alert")).toHaveTextContent(
      "Position already occupied by bead A1 in A.",
    );
    expect(within(dialog).getByRole("alert")).toHaveTextContent("change Scope");
    await user.click(within(dialog).getByRole("button", { name: "Dismiss" }));
    await user.click(within(dialog).getByRole("button", { name: "A atom OP1" }));
    expect(useModel).toBeEnabled();
  });

  it("keeps connections in sync with the beads", async () => {
    const { user, dialog } = await openCreator();

    expect(
      within(dialog).queryByRole("tab", { name: "Connectivity" }),
    ).not.toBeInTheDocument();
    await openBeadSettings(user, dialog);
    await user.clear(within(dialog).getByLabelText("Bead ID"));
    await user.type(within(dialog).getByLabelText("Bead ID"), "P1");
    await user.click(within(dialog).getByRole("button", { name: "Connect beads" }));
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead P1 P" }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead A2 C4'" }),
    );
    await user.click(within(dialog).getByRole("button", { name: "JSON preview" }));
    expect(
      within(dialog).getByText(/"intra_residue": \[\s*\[\s*"A2"/),
    ).toBeInTheDocument();
  });

  it("edits a model loaded from JSON and discards changes on cancel", async () => {
    const app = renderApp("/");
    const { user } = app;
    await user.click(await screen.findByRole("button", { name: "Custom model" }));
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
    await openModelDetails(user, dialog);
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

    expect(within(dialog).getByLabelText("Model actions menu")).toHaveAttribute(
      "title",
      "1 model issue",
    );
    await openModelMenu(user, dialog);
    await user.click(
      within(dialog).getByRole("button", {
        name: "Remove invalid connections",
      }),
    );
    expect(issue).not.toBeInTheDocument();
    expect(within(dialog).getByLabelText("Model actions menu")).toHaveAttribute(
      "title",
      "Model ready",
    );
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeEnabled();
  });

  it("blocks a model that exceeds the byte size limit", async () => {
    const { user, dialog } = await openCreator();

    await openModelDetails(user, dialog);
    await user.click(within(dialog).getByLabelText("Model name"));
    await user.paste("€".repeat(2500));

    expect(
      within(dialog).getByText("The model definition exceeds the 8 KiB limit."),
    ).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeDisabled();
    await openModelMenu(user, dialog);
    expect(
      within(dialog).getByRole("button", { name: "Export model as JSON" }),
    ).toBeDisabled();
  });

  it("keeps editing when Enter is pressed in a creator field", async () => {
    const { user } = renderApp("/");
    await user.click(await screen.findByRole("tab", { name: "Use example" }));
    await user.click(screen.getByRole("radio", { name: "1EHZ" }));
    await user.click(screen.getByRole("button", { name: "Custom model" }));
    await user.click(screen.getByRole("button", { name: "Open creator" }));
    await user.click(screen.getByRole("button", { name: "Use model" }));
    await user.click(screen.getByRole("button", { name: "Edit" }));
    const dialog = screen.getByRole("dialog", { name: "Model creator" });

    await openModelDetails(user, dialog);
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

    await openBeadSettings(user, dialog);
    const bead = await within(dialog).findByRole("article", { name: "Bead A1" });
    const extraAtom = within(bead).getByRole("button", { name: "O1P" });
    expect(extraAtom).toHaveAttribute("aria-pressed", "true");

    await user.click(extraAtom);
    expect(within(bead).queryByRole("button", { name: "O1P" })).not.toBeInTheDocument();
  });

  it("explains why a loaded model cannot be edited", async () => {
    const { user } = renderApp("/");
    await user.click(await screen.findByRole("button", { name: "Custom model" }));
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
    await openModelDetails(user, dialog);
    const nameField = within(dialog).getByRole("textbox", { name: "Model name" });

    await openModelMenu(user, dialog);
    await user.click(
      within(dialog).getByRole("button", { name: "Start from scratch" }),
    );
    await openBeadSettings(user, dialog);
    expect(nameField).toHaveValue("");
    expect(
      within(dialog)
        .getAllByRole("article")
        .map((bead) => bead.ariaLabel),
    ).toEqual(["Bead A1"]);
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeDisabled();

    await openModelMenu(user, dialog);
    await user.click(
      within(dialog).getByRole("button", { name: "Load SimRNA template" }),
    );
    await openBeadSettings(user, dialog);
    expect(nameField).toHaveValue("Custom Model");
    expect(within(dialog).getAllByRole("article")).toHaveLength(1);
    await user.click(within(dialog).getByLabelText("Select bead"));
    expect(
      within(
        within(dialog).getByRole("menu", { name: "Available beads" }),
      ).getAllByRole("menuitemradio"),
    ).toHaveLength(7);
    expect(within(dialog).getByRole("button", { name: "Use model" })).toBeEnabled();
  });

  it("edits atoms and connections directly on the nucleotide diagram", async () => {
    const { user, dialog } = await openCreator();
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead A1 P" }),
    );
    await openBeadSettings(user, dialog);
    const bead = within(dialog).getByRole("article", { name: "Bead A1" });
    await user.selectOptions(
      within(bead).getByLabelText("Strategy"),
      "geometric_center",
    );
    await user.click(within(dialog).getByRole("button", { name: "A atom OP1" }));
    expect(within(bead).getByRole("button", { name: "OP1" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(within(dialog).getByRole("button", { name: "G atom OP1" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await user.click(within(dialog).getByRole("button", { name: "Connect beads" }));
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead A1 P" }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: "Select A bead A2 C4'" }),
    );
    await user.click(within(dialog).getByRole("button", { name: "JSON preview" }));
    expect(
      within(dialog).getByText(/"intra_residue": \[\s*\[\s*"A2"/),
    ).toBeInTheDocument();
  });
});
