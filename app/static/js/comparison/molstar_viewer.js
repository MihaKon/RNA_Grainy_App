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

  function createRepresentationConfig(entry, representationType) {
    if (!representationTypes.has(representationType)) {
      throw new Error(
        `Unsupported representation type: ${representationType}`,
      );
    }

    const typeParams = {};

    if (entry.isCoarse) {
      typeParams.excludeTypes = ["computed"];
    }

    return {
      type: representationType,
      typeParams
    };
  }

  function getStructureEntry(structureId) {
    const structure = structureEntries.get(structureId)
    if (!structure) {
      throw new Error(`Unknown Mol* structure ${structureId}`);
    }
    return structure;
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

  async function setStructureRepresentation(
    structureId,
    representationType,
  ) {
    const entry = getStructureEntry(structureId);

    if (entry.representationType === representationType) {
      return;
    }

    const polymerComponent = entry.components.find(
      component => component.type === "polymer",
    );

    if (!polymerComponent) {
      throw new Error(
        `Polymer component not found for ${structureId}`,
      );
    }

    const newRepresentation =
      await plugin.builders.structure.representation.addRepresentation(
        polymerComponent.selector,
        createRepresentationConfig(
          entry,
          representationType,
        ),
        {
          tag:
            `rnagrainy-${structureId}-polymer-` +
            `${representationType}`,
        },
      );

    if (!newRepresentation) {
      throw new Error(
        `Could not create ${representationType} representation ` +
          `for ${structureId}`,
      );
    }

    plugin.state.data.updateCellState(
      newRepresentation.ref,
      {
        isHidden: !entry.visible,
      },
    );

    const update = plugin.state.data.build();
    update.delete(polymerComponent.representation.ref);
    await update.commit();

    polymerComponent.representation = newRepresentation;
    entry.representationType = representationType;
  }

  for (const structureData of structures) {
    if (!structureData.id) {
      throw new Error(`Every Mol* structure must have and id.`);
    }

    if (structureEntries.has(structureData.id)) {
      throw new Error(`Duplicate Mol* structure id ${structureData.id}`)
    }

    const data = await plugin.builders.data.download(
      {
        url: structureData.url,
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
      isCoarse: structureData.isCoarse,
      visible: true,
    };

    for (const componentType of componentTypes) {
      const component =
        await plugin.builders.structure.tryCreateComponentStatic(
          structure,
          componentType,
        );

      if (!component) {
        continue;
      }

      const representation =
        await plugin.builders.structure.representation.addRepresentation(
          component,
          createRepresentationConfig(
            entry,
            "ball-and-stick",
          ),
          {
            tag:
              `rnagrainy-${structureData.id}-` +
              `${componentType}-representation`,
          },
        );

      if (!representation) {
        continue;
      }

      entry.components.push({
        type: componentType,
        selector: component,
        representation
      });

    }

    structureEntries.set(structureData.id, entry);
  }

  return Object.freeze({
    setStructureVisibility,
    setStructureRepresentation,

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
