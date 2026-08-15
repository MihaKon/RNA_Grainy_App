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

  for (const structureData of structures) {
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

    const representation = {
      type: "ball-and-stick",
      typeParams: {},
    };

    if (structureData.isCoarse) {
      representation.typeParams.excludeTypes = ["computed"];
    }

    await plugin.builders.structure.representation.addRepresentation(
      structure,
      representation,
    );
  }

  return viewer;
};
