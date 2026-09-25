window.createMolstarViewer = async function (containerId, structures) {
  const viewer = await molstar.Viewer.create(containerId, {
    layoutIsExpanded: false,
    layoutShowControls: false,
    layoutShowRemoteState: false,
    layoutShowSequence: true,
    layoutShowLeftPanel: true,
    layoutShowLog: false,
    viewportShowExpand: true,
    viewportShowSelectionMode: true,
    viewportShowAnimation: false,
    pdbProvider: "rcsb",
    emdbProvider: "rcsb",
  });

  const plugin = viewer.plugin;
  const structureEntries = new Map();

  const componentTypes = [
    "polymer",
    "ligand",
    "non-standard",
    "branched",
    "water",
    "ion",
  ];

  const representationTypes = new Set([
    "ball-and-stick",
    "cartoon",
    "backbone",
  ]);

  const colorModes = new Set([
    "uniform",
    "element-symbol",
  ]);

  const structureColors = {
    reference: 0x047857,
    coarse: 0xf97316,
  };

  function getStructureEntry(structureId) {
    const entry = structureEntries.get(structureId);

    if (!entry) {
      throw new Error(`Unknown Mol* structure ${structureId}`);
    }

    return entry;
  }

  function createRepresentationConfig(entry, representationType, colorMode) {
    if (!representationTypes.has(representationType)) {
      throw new Error(
        `Unsupported representation type: ${representationType}`,
      );
    }

    const typeParams = {};

    if (entry.isCoarse) {
      typeParams.excludeTypes = ["computed"];
    }

    const config = {
      type: representationType,
      typeParams,
      color: colorMode,
    };

    if (colorMode === "uniform") {
      config.colorParams = {
        value: entry.uniformColor,
      };
    }

    return config;
  }

  async function updateComponentRepresentation(
    entry,
    component,
    representationType,
    colorMode,
  ) {
    const representation =
      await plugin.builders.structure.representation.addRepresentation(
        component.selector,
        createRepresentationConfig(
          entry,
          representationType,
          colorMode,
        ),
        {
          tag: component.tag,
        },
      );

    if (!representation) {
      throw new Error(
        `Could not create ${representationType} representation ` +
          `for ${component.type}`,
      );
    }

    plugin.state.data.updateCellState(representation.ref, {
      isHidden: !entry.visible,
    });

    component.representation = representation;
  }

  function setStructureVisibility(structureId, visible) {
    if (typeof visible !== "boolean") {
      throw new TypeError("visible must be a boolean");
    }

    const entry = getStructureEntry(structureId);
    entry.visible = visible;

    for (const component of entry.components) {
      plugin.state.data.updateCellState(
        component.representation.ref,
        {
          isHidden: !visible,
        },
      );
    }
  }

  async function setStructureRepresentation(structureId, representationType) {
    if (!representationTypes.has(representationType)) {
      throw new Error(
        `Unsupported representation type: ${representationType}`,
      );
    }

    const entry = getStructureEntry(structureId);

    if (entry.representationType === representationType) {
      return;
    }

    const polymerComponent = entry.components.find(
      (component) => component.type === "polymer",
    );

    if (!polymerComponent) {
      throw new Error(
        `Polymer component not found for ${structureId}`,
      );
    }

    await updateComponentRepresentation(
      entry,
      polymerComponent,
      representationType,
      entry.colorMode,
    );

    entry.representationType = representationType;
  }

  async function setStructureColoring(structureId, colorMode) {
    if (!colorModes.has(colorMode)) {
      throw new Error(`Unsupported color mode: ${colorMode}`);
    }

    const entry = getStructureEntry(structureId);

    if (entry.colorMode === colorMode) {
      return;
    }

    for (const component of entry.components) {
      const representationType =
        component.type === "polymer"
          ? entry.representationType
          : "ball-and-stick";

      await updateComponentRepresentation(
        entry,
        component,
        representationType,
        colorMode,
      );
    }

    entry.colorMode = colorMode;
  }

  for (const structureData of structures) {
    if (!structureData.id) {
      throw new Error("Every Mol* structure must have an id.");
    }

    if (structureEntries.has(structureData.id)) {
      throw new Error(
        `Duplicate Mol* structure id ${structureData.id}`,
      );
    }

    const data = await plugin.builders.data.download(
      {
        url: structureData.url,
        label: structureData.label,
      },
      {
        state: {
          isGhost: true,
        },
      },
    );

    const trajectory = await plugin.builders.structure.parseTrajectory(
      data,
      structureData.format,
    );

    const model = await plugin.builders.structure.createModel(trajectory);
    const structure = await plugin.builders.structure.createStructure(model);

    const entry = {
      structure,
      components: [],
      representationType: "ball-and-stick",
      colorMode: "uniform",
      uniformColor: structureData.isCoarse
        ? structureColors.coarse
        : structureColors.reference,
      isCoarse: structureData.isCoarse,
      visible: true,
    };

    for (const componentType of componentTypes) {
      const selector =
        await plugin.builders.structure.tryCreateComponentStatic(
          structure,
          componentType,
        );

      if (!selector) {
        continue;
      }

      const component = {
        type: componentType,
        selector,
        tag:
          `rnagrainy-${structureData.id}-` +
          `${componentType}-representation`,
        representation: null,
      };

      await updateComponentRepresentation(
        entry,
        component,
        "ball-and-stick",
        entry.colorMode,
      );

      entry.components.push(component);
    }

    structureEntries.set(structureData.id, entry);
  }

  return Object.freeze({
    setStructureVisibility,
    setStructureRepresentation,
    setStructureColoring,

    getStructureColoring(structureId) {
      return getStructureEntry(structureId).colorMode;
    },

    getStructure(structureId) {
      return getStructureEntry(structureId).structure;
    },

    isStructureVisible(structureId) {
      return getStructureEntry(structureId).visible;
    },

    getRepresentationType(structureId) {
      return getStructureEntry(structureId).representationType;
    },

    getStructureIds() {
      return [...structureEntries.keys()];
    },

    dispose() {
      structureEntries.clear();
      viewer.dispose();
    },
  });
};
