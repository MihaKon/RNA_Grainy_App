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
      typeParams.excludeTypes = ["computed"]
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

  function setStructureVisibility(structureId, visible){
    if (typeof visible !== "boolean") {
      throw new TypeError("visible must be a boolean");
    }

    const entry = getStructureEntry(structureId);
    entry.visible = visible;
    plugin.state.data.updateCellState(
      entry.representation.ref,
      {
        isHidden: !visible,
      },
    );
  }

  async function setStructureRepresentation(structureId, representationType,){
    const entry = getStructureEntry(structureId);
    if (entry.representationType === representationType){
      return;
    }

    const representation = await plugin.builders.structure.representation.addRepresentation(
        entry.structure,
        createRepresentationConfig(
          entry,
          representationType,
        ),
        {
          tag: entry.representationTag,
        },
      );

    if (!representation) {
      throw new Error(
        `Could not create ${representationType} representation ` +
          `for ${structureId}`,
      );
    }

    entry.representation = representation;
    entry.representationType = representationType;

    plugin.state.data.updateCellState(
      representation.ref,
      {
        isHidden: !entry.visible,
      },
    );
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
      representation: null,
      representationTag: `rnagrainy-${structureData.id}-representation`,
      representationType: null,
      isCoarse: structureData.isCoarse,
      visible: true,
    };

    entry.representation = await plugin.builders.structure.representation.addRepresentation(
      structure,
      createRepresentationConfig(entry, 'ball-and-stick'),
      {
        tag: entry.representationTag,
      },
    );
    entry.representationType = "ball-and-stick";

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
