import "molstar/build/viewer/molstar.css";
import "./molstarOverrides.css";

import type { Trajectory } from "molstar/lib/mol-model/structure";
import { PluginConfig } from "molstar/lib/mol-plugin/config";
import type { BuiltInTrajectoryFormat } from "molstar/lib/mol-plugin-state/formats/trajectory";
import { createPluginUI } from "molstar/lib/mol-plugin-ui";
import type { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import { renderReact18 } from "molstar/lib/mol-plugin-ui/react18";
import { DefaultPluginUISpec } from "molstar/lib/mol-plugin-ui/spec";
import { MolScriptBuilder as MS } from "molstar/lib/mol-script/language/builder";
import type { StateObjectSelector } from "molstar/lib/mol-state";
import { Color } from "molstar/lib/mol-util/color";

import { MolstarViewportControls } from "./MolstarViewportControls";

export type StructureId = "reference" | "coarse";
export type RepresentationType = "ball-and-stick" | "cartoon" | "backbone";
export type ColorMode = "uniform" | "element-symbol" | "chain-id" | "residue-name";

export interface StructureInput {
  id: StructureId;
  data: string;
  format: BuiltInTrajectoryFormat;
  color: number;
  isCoarse: boolean;
}

export interface MolstarViewer {
  readonly failedStructures: readonly StructureId[];
  readonly modelNumbers: readonly number[];
  readonly hasNonPolymer: boolean;
  setVisibility(id: StructureId, visible: boolean): void;
  setNonPolymerVisibility(visible: boolean): void;
  setModel(index: number): Promise<void>;
  setRepresentation(id: StructureId, type: RepresentationType): Promise<void>;
  setColorMode(id: StructureId, colorMode: ColorMode): Promise<void>;
  dispose(): void;
}

type StructureSelector = Awaited<
  ReturnType<PluginUIContext["builders"]["structure"]["createStructure"]>
>;

type ModelSelector = Awaited<
  ReturnType<PluginUIContext["builders"]["structure"]["createModel"]>
>;

type ComponentSelector = Awaited<
  ReturnType<
    PluginUIContext["builders"]["structure"]["tryCreateComponentFromExpression"]
  >
>;

interface StructureEntry {
  model: ModelSelector;
  modelNumbers: readonly number[];
  polymer: StructureSelector;
  nonPolymer: ComponentSelector;
  representation: StateObjectSelector | undefined;
  nonPolymerRepresentation: StateObjectSelector | undefined;
  representationType: RepresentationType;
  colorMode: ColorMode;
  color: number;
  isCoarse: boolean;
  visible: boolean;
}

const IS_POLYMER = MS.core.rel.eq([MS.ammp("entityType"), "polymer"]);
const POLYMER_EXPRESSION = MS.struct.generator.atomGroups({
  "entity-test": IS_POLYMER,
});
const NON_POLYMER_EXPRESSION = MS.struct.generator.atomGroups({
  "entity-test": MS.core.logic.not([IS_POLYMER]),
});

export async function createMolstarViewer(
  target: HTMLElement,
  structures: readonly StructureInput[],
): Promise<MolstarViewer> {
  const plugin = await createPluginUI({
    target,
    render: renderReact18,
    spec: {
      ...DefaultPluginUISpec(),
      components: {
        viewport: {
          controls: MolstarViewportControls,
        },
      },
      layout: {
        initial: { isExpanded: false, showControls: false },
      },
      canvas3d: {
        renderer: { backgroundColor: Color(0xffffff) },
      },
      config: [
        [PluginConfig.Viewport.ShowExpand, true],
        [PluginConfig.Viewport.ShowSelectionMode, true],
        [PluginConfig.Viewport.ShowAnimation, false],
        [PluginConfig.Viewport.ShowTrajectoryControls, true],
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

  let nonPolymerVisible = false;

  const setHidden = (
    representation: StateObjectSelector | undefined,
    hidden: boolean,
  ) => {
    if (!representation) return;
    plugin.state.data.updateCellState(representation.ref, { isHidden: hidden });
  };

  const applyVisibility = (entry: StructureEntry) => {
    setHidden(entry.representation, !entry.visible);
    setHidden(entry.nonPolymerRepresentation, !entry.visible || !nonPolymerVisible);
  };

  const updateRepresentation = async (
    id: StructureId,
    representationType: RepresentationType,
    colorMode: ColorMode,
  ) => {
    const entry = getEntry(id);
    const colorProps = {
      color: colorMode,
      ...(colorMode === "uniform" && {
        colorParams: { value: Color(entry.color) },
      }),
    };
    entry.representation =
      await plugin.builders.structure.representation.addRepresentation(
        entry.polymer,
        {
          type: representationType,
          typeParams: entry.isCoarse ? { excludeTypes: ["computed"] } : {},
          ...colorProps,
        },
        { tag: `rnagrainy-${id}-representation` },
      );
    if (entry.nonPolymer) {
      entry.nonPolymerRepresentation =
        await plugin.builders.structure.representation.addRepresentation(
          entry.nonPolymer,
          { type: "ball-and-stick", ...colorProps },
          { tag: `rnagrainy-${id}-non-polymer-representation` },
        );
    }

    entry.representationType = representationType;
    entry.colorMode = colorMode;
    applyVisibility(entry);
  };

  const loadStructure = async (input: StructureInput) => {
    const data = await plugin.builders.data.rawData(
      { data: input.data, label: input.id },
      { state: { isGhost: true } },
    );
    try {
      const trajectory = await plugin.builders.structure.parseTrajectory(
        data,
        input.format,
      );
      const model = await plugin.builders.structure.createModel(trajectory);
      const structure = await plugin.builders.structure.createStructure(model);
      const polymer = input.isCoarse
        ? undefined
        : await plugin.builders.structure.tryCreateComponentFromExpression(
            structure,
            POLYMER_EXPRESSION,
            "rnagrainy-polymer",
          );
      const nonPolymer = polymer
        ? await plugin.builders.structure.tryCreateComponentFromExpression(
            structure,
            NON_POLYMER_EXPRESSION,
            "rnagrainy-non-polymer",
          )
        : undefined;

      entries.set(input.id, {
        model,
        modelNumbers: readModelNumbers(trajectory.data),
        polymer: polymer ?? structure,
        nonPolymer,
        representation: undefined,
        nonPolymerRepresentation: undefined,
        representationType: "ball-and-stick",
        colorMode: "uniform",
        color: input.color,
        isCoarse: input.isCoarse,
        visible: true,
      });
      await updateRepresentation(input.id, "ball-and-stick", "uniform");
    } catch (error) {
      entries.delete(input.id);
      await plugin.build().delete(data).commit();
      throw error;
    }
  };

  const failedStructures: StructureId[] = [];
  const errors: unknown[] = [];
  for (const input of structures) {
    try {
      await loadStructure(input);
    } catch (error) {
      failedStructures.push(input.id);
      errors.push(error);
    }
  }

  if (entries.size === 0) {
    plugin.dispose();
    throw new AggregateError(errors, "None of the structures could be loaded.");
  }

  const modelNumbers = entries.values().next().value?.modelNumbers ?? [1];

  return {
    failedStructures,
    modelNumbers,
    hasNonPolymer: [...entries.values()].some((entry) => entry.nonPolymer),
    setNonPolymerVisibility(visible) {
      nonPolymerVisible = visible;
      entries.forEach(applyVisibility);
    },
    async setModel(index) {
      const update = plugin.build();
      for (const entry of entries.values()) {
        if (index < entry.modelNumbers.length) {
          update.to(entry.model).update({ modelIndex: index });
        }
      }
      await update.commit();
    },
    setVisibility(id, visible) {
      const entry = getEntry(id);
      entry.visible = visible;
      applyVisibility(entry);
    },
    async setRepresentation(id, type) {
      const entry = getEntry(id);
      if (entry.representationType !== type) {
        await updateRepresentation(id, type, entry.colorMode);
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

function readModelNumbers(trajectory: Trajectory | undefined): number[] {
  if (!trajectory) return [1];
  return Array.from({ length: trajectory.frameCount }, (_, index) => {
    const frame = trajectory.getFrameAtIndex(index);
    return "modelNum" in frame ? frame.modelNum : index + 1;
  });
}
