const JsonBuilder = {
  getAtomsForScope(scope) {
    return ATOM_DEFINITIONS[scope];
  },

  copy(obj){
    return JSON.parse(JSON.stringify(obj));
  },

  buildJson(state) {
    const json = {
      model_name: state.modelName,
      description: state.modelDescription,
      default_mapping: {
        residues: ["A", "G", "C", "U"],
        config: {
          bead_names: {},
          atom_centers: {},
          description: {},
          strategies: {},
        },
      },
      mapping: [],
      connectivity: {
        intra_residue: state.intra_residues,
        inter_residue: [],
      },
    };

    state.beads.forEach((b) => {
      const id = b.beadID;

      if (["all", "phosphate", "sugar"].includes(b.scope)) {
        json.default_mapping.config.bead_names[id] = b.name;
        json.default_mapping.config.atom_centers[id] = b.atoms;
        json.default_mapping.config.description[id] = b.description;
        json.default_mapping.config.strategies[id] = b.strategy;
      } else if (b.scope in SCOPE_RESIDUES_MAP) {
        const targetResidues = SCOPE_RESIDUES_MAP[b.scope];
        let mappingRecord = json.mapping.find(
          (m) => JSON.stringify(m.residues) === JSON.stringify(targetResidues),
        );

        if (!mappingRecord) {
          mappingRecord = {
            residues: targetResidues,
            config: {
              bead_names: {},
              atom_centers: {},
              description: {},
              strategies: {},
            },
          };
          json.mapping.push(mappingRecord);
        }

        mappingRecord.config.bead_names[id] = b.name;
        mappingRecord.config.atom_centers[id] = b.atoms;
        mappingRecord.config.description[id] = b.description;
        mappingRecord.config.strategies[id] = b.strategy;
      }
    });

    const validInterResidues = state.inter_residues.filter(
      (pair) => pair.source && pair.target,
    );

    if (validInterResidues.length > 0) {
      json.connectivity.inter_residue = validInterResidues.map((pair) => ({
        source: pair.source,
        target: pair.target,
      }));
    }

    return json;
  },

  downloadConfig(jsonObj, filename) {
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(jsonObj, null, 2));
    const node = document.createElement("a");
    const safeName = (filename || "custom_model").replace(/\s+/g, "_").toLowerCase();

    node.setAttribute("href", dataStr);
    node.setAttribute("download", safeName + ".json");
    document.body.appendChild(node);
    node.click();
    node.remove();
  },
};
