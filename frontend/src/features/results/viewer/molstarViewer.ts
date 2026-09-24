import "molstar/build/viewer/theme/dark.css";

import type { StateObjectSelector } from "molstar/lib/mol-state";
import type { BuiltInTrajectoryFormat } from "molstar/lib/mol-plugin-state/formats/trajectory";
import { createPluginUI } from "molstar/lib/mol-plugin-ui";
import type { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import { renderReact18 } from "molstar/lib/mol-plugin-ui/react18";
import { DefaultPluginUISpec } from "molstar/lib/mol-plugin-ui/spec";
import { PluginConfig } from "molstar/lib/mol-plugin/config";
import { Color } from "molstar/lib/mol-util/color";

export type StructureId = "reference" | "coarse";
export type RepresentationType = "ball-and-stick" | "cartoon" | "backbone";
export type ColorMode = "uniform" | "element-symbol";

export interface StructureInput {
  id: StructureId;
  data: string;
  format: BuiltInTrajectoryFormat;
  color: number;
  isCoarse: boolean;
}

export interface MolstarViewer {
  setVisibility(id: StructureId, visible: boolean): void;
  setRepresentation(type: RepresentationType): Promise<void>;
  setColorMode(id: StructureId, colorMode: ColorMode): Promise<void>;
  dispose(): void;
}

type StructureSelector = Awaited<
  ReturnType<PluginUIContext["builders"]["structure"]["createStructure"]>
>;

interface StructureEntry {
  structure: StructureSelector;
  representation: StateObjectSelector | undefined;
  representationType: RepresentationType;
  colorMode: ColorMode;
  color: number;
  isCoarse: boolean;
  visible: boolean;
}

export const VIEWER_BACKGROUND = 0x002b45;

export async function createMolstarViewer(
  target: HTMLElement,
  structures: readonly StructureInput[],
): Promise<MolstarViewer> {
  const plugin = await createPluginUI({
    target,
    render: renderReact18,
    spec: {
      ...DefaultPluginUISpec(),
      layout: {
        initial: { isExpanded: false, showControls: false },
      },
      canvas3d: {
        renderer: { backgroundColor: Color(VIEWER_BACKGROUND) },
      },
      config: [
        [PluginConfig.Viewport.ShowExpand, true],
        [PluginConfig.Viewport.ShowSelectionMode, true],
        [PluginConfig.Viewport.ShowAnimation, false],
        [PluginConfig.Viewport.ShowTrajectoryControls, false],
        [PluginConfig.Viewport.ShowXR, "never"],
      ],
    },
  });

  const entries = new Map<StructureId, StructureEntry>();

  const getEntry = (id: StructureId): StructureEntry => {
    const entry = entries.get(id);
    if (!entry) throw new Error(`Unknown structure: ${id}`);
    return entry;
  };

  const applyVisibility = (entry: StructureEntry) => {
    if (!entry.representation) return;
    plugin.state.data.updateCellState(entry.representation.ref, {
      isHidden: !entry.visible,
    });
  };

  // Replaces the structure's representation by reusing its tag, so only one is ever shown.
  const updateRepresentation = async (
    id: StructureId,
    representationType: RepresentationType,
    colorMode: ColorMode,
  ) => {
    const entry = getEntry(id);
    const representation =
      await plugin.builders.structure.representation.addRepresentation(
        entry.structure,
        {
          type: representationType,
          typeParams: entry.isCoarse ? { excludeTypes: ["computed"] } : {},
          color: colorMode,
          ...(colorMode === "uniform" && {
            colorParams: { value: Color(entry.color) },
          }),
        },
        { tag: `rnagrainy-${id}-representation` },
      );

    entry.representation = representation;
    entry.representationType = representationType;
    entry.colorMode = colorMode;
    applyVisibility(entry);
  };

  try {
    for (const input of structures) {
      const data = await plugin.builders.data.rawData(
        { data: input.data, label: input.id },
        { state: { isGhost: true } },
      );
      const trajectory = await plugin.builders.structure.parseTrajectory(
        data,
        input.format,
      );
      const model = await plugin.builders.structure.createModel(trajectory);
      const structure = await plugin.builders.structure.createStructure(model);

      entries.set(input.id, {
        structure,
        representation: undefined,
        representationType: "ball-and-stick",
        colorMode: "uniform",
        color: input.color,
        isCoarse: input.isCoarse,
        visible: true,
      });
      await updateRepresentation(input.id, "ball-and-stick", "uniform");
    }
  } catch (error) {
    plugin.dispose();
    throw error;
  }

  return {
    setVisibility(id, visible) {
      const entry = getEntry(id);
      entry.visible = visible;
      applyVisibility(entry);
    },
    async setRepresentation(type) {
      for (const [id, entry] of entries) {
        if (entry.representationType !== type) {
          await updateRepresentation(id, type, entry.colorMode);
        }
      }
    },
    async setColorMode(id, colorMode) {
      const entry = getEntry(id);
      if (entry.colorMode !== colorMode) {
        await updateRepresentation(id, entry.representationType, colorMode);
      }
    },
    dispose() {
      entries.clear();
      plugin.dispose();
    },
  };
}
