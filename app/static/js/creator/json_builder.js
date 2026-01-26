const JsonBuilder = {
  getAtomsForScope(scope) {
    return ATOM_DEFINITIONS[scope];
  },

  copy(obj){
    return JSON.parse(JSON.stringify(obj));
  },
  
 inferScope(residues, atoms = []) {
    const resScope = this.determineScopeByResidues(residues);

    if (resScope === "all" && atoms.length > 0) {
      const isPhosphate = atoms.every(atom => ATOM_DEFINITIONS.phosphate.includes(atom));
      if (isPhosphate) return "phosphate";

      const isSugar = atoms.every(atom => ATOM_DEFINITIONS.sugar.includes(atom));
      if (isSugar) return "sugar";
    }

    return resScope;
  },

  determineScopeByResidues(residues) {
    if (!residues || !Array.isArray(residues)) return "all";
    const sortedRes = [...residues].map(r => r.toUpperCase()).sort();
    const resStr = JSON.stringify(sortedRes);

    for (const [scopeKey, scopeResidues] of Object.entries(SCOPE_RESIDUES_MAP)) {
      const sortedScopeRes = [...scopeResidues].map(r => r.toUpperCase()).sort();
      if (JSON.stringify(sortedScopeRes) === resStr) return scopeKey;
    }
    return "all";
  },

  buildJsonFromFile(json) {
    const beads = [];

    const processConfig = (config, residues) => {
      if (!config || !config.bead_names) return;

      Object.keys(config.bead_names).forEach((beadID) => {
        const atoms = config.atom_centers?.[beadID] || [];
        const dynamicScope = this.inferScope(residues, atoms);

        beads.push({
          beadID: beadID,
          name: config.bead_names[beadID] || beadID,
          scope: dynamicScope,
          description: config.description?.[beadID] || "",
          strategy: config.strategies?.[beadID] || "direct",
          atoms: atoms,
        });
      });
    };

    processConfig(json.default_mapping?.config, json.default_mapping?.residues);

    if (json.mapping && Array.isArray(json.mapping)) {
      json.mapping.forEach(m => processConfig(m.config, m.residues));
    }

    return {
      name: json.model_name || "Imported Model",
      description: json.description || "",
      beads: beads,
      intra_residues: json.connectivity?.intra_residue || [],
      inter_residues: json.connectivity?.inter_residue || []
    };
  },

  buildJsonFromState(state) {
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
