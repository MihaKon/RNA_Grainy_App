import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { Structure } from "molstar/lib/mol-model/structure";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import { DefaultPluginUISpec } from "molstar/lib/mol-plugin-ui/spec";
import { SuperpositionControls } from "molstar/lib/mol-plugin-ui/structure/superposition";
import { expect, it, vi } from "vitest";

import { createDefaultDraft } from "@/features/creator/modelDraft";
import { buildPreview, readPreviewSource } from "@/features/creator/previewStructure";

import { createMolstarViewer } from "./molstarViewer";

vi.mock("molstar/lib/mol-plugin-ui", () => ({
  createPluginUI: vi.fn(),
}));

it("superposes the input and CG structures through Molstar controls", async () => {
  const { createPluginUI } = await import("molstar/lib/mol-plugin-ui");
  const plugin = new PluginUIContext(DefaultPluginUISpec());
  await plugin.init();
  vi.mocked(createPluginUI).mockResolvedValue(plugin);
  const source = await readPreviewSource(
    readFileSync(
      resolve(import.meta.dirname, "../../../../../app/static/presets/1EHZ.cif"),
      "utf8",
    ),
  );
  const preview = buildPreview(createDefaultDraft(), source.residues, "all");
  try {
    const viewer = await createMolstarViewer(document.createElement("div"), [
      {
        id: "reference",
        data: preview.reference,
        format: "mmcif",
        color: 0x0091c9,
        isCoarse: false,
      },
      {
        id: "coarse",
        data: preview.coarse,
        format: "mmcif",
        color: 0xd89425,
        isCoarse: true,
      },
    ]);
    expect(viewer.failedStructures).toEqual([]);
    const structures = plugin.managers.structure.hierarchy.current.structures;
    expect(structures).toHaveLength(2);
    for (const entry of structures) {
      const structure = entry.components[0]?.cell.obj?.data ?? entry.cell.obj?.data;
      if (!structure) throw new Error("Missing loaded structure");
      plugin.managers.structure.selection.fromLoci(
        "add",
        Structure.toStructureElementLoci(structure),
      );
    }
    const controls = new SuperpositionControls({}, plugin);
    vi.spyOn(controls, "cameraReset").mockResolvedValue(undefined);
    controls.state.options = {
      ...controls.state.options,
      traceOnly: false,
      alignSequences: false,
    };
    expect(controls.chainEntries).toHaveLength(2);
    await controls.superposeChains();
    expect(
      plugin.state.data.selectQ((query) =>
        query.root
          .subtree()
          .withTransformer(StateTransforms.Model.TransformStructureConformation),
      ),
    ).toHaveLength(1);
  } finally {
    plugin.dispose();
  }
}, 20000);
