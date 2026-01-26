document.addEventListener("alpine:init", () => {
  Alpine.data("modelCreator", () => ({
    // === State === //
    get showCreator() {
      return Alpine.store("openCreator").isOpen;
    },
    activeTab: "beads",

    // === Default Custom Model Data === //
    modelName: DEFAULT_MODEL.name,
    modelDescription: DEFAULT_MODEL.description,
    beads: JsonBuilder.copy(DEFAULT_MODEL.beads),
    intra_residues: JsonBuilder.copy(DEFAULT_MODEL.intra_residues),
    inter_residues: JsonBuilder.copy(DEFAULT_MODEL.inter_residues),

    /// === Helpers For HTML === //
    getAvailableScopes() {
      return SCOPE_OPTIONS;
    },

    getJsonChars() {
      return JSON.stringify(JsonBuilder.buildJsonFromState(this), null, 2).length;
    },

    getStrategyLabel(val) {
      return STRATEGY_OPTIONS.find((opt) => opt.value === val).label;
    },

    getAtomsForScope(scope) {
      return JsonBuilder.getAtomsForScope(scope);
    },

    getUniqueBeads() {
      const seen = new Set();
      return this.beads.filter((b) => {
        const duplicate = seen.has(b.beadID);
        seen.add(b.beadID);
        return !duplicate;
      });
    },

    hasIntraConnection(id1, id2) {
      return this.intra_residues.some(
        (pair) =>
          (pair[0] === id1 && pair[1] === id2) ||
          (pair[0] === id2 && pair[1] === id1),
      );
    },

    isInterSource(id) {
      return (
        this.inter_residues.length > 0 && this.inter_residues[0].source === id
      );
    },

    isInterTarget(id) {
      return (
        this.inter_residues.length > 0 && this.inter_residues[0].target === id
      );
    },

    // === Bead Actions === //
    addBead() {
      const newID = "A" + (this.beads.length + 1);
      this.beads.push({
        beadID: newID,
        name: newID,
        scope: "all",
        description: "",
        strategy: "direct",
        atoms: [],
      });
    },

    removeBead(index) {
      const idToRemove = this.beads[index].beadID;
      this.beads.splice(index, 1);

      this.intra_residues = this.intra_residues.filter(
        (pair) => !pair.includes(idToRemove),
      );
      this.inter_residues = this.inter_residues.filter(
        (link) => link.source !== idToRemove && link.target !== idToRemove,
      );
    },

    toggleAtom(bead, atom) {
      if (bead.atoms.includes(atom)) {
        bead.atoms = bead.atoms.filter((a) => a !== atom);
        return;
      }
      if (bead.strategy === "direct") {
        bead.atoms = [atom];
      } else {
        bead.atoms.push(atom);
      }
    },

    /// === Connectivity Actions === //
    toggleIntraConnection(id1, id2) {
      if (id1 === id2) return;

      const index = this.intra_residues.findIndex(
        (pair) =>
          (pair[0] === id1 && pair[1] === id2) ||
          (pair[0] === id2 && pair[1] === id1),
      );

      if (index !== -1) {
        this.intra_residues.splice(index, 1);
      } else {
        this.intra_residues.push([id1, id2]);
      }
    },

    setInterConnection(sourceID, targetID) {
      const current = this.inter_residues[0] || {};
      const newSource =
        sourceID !== undefined ? sourceID : current.source || null;
      const newTarget =
        targetID !== undefined ? targetID : current.target || null;

      this.inter_residues = [
        {
          source: newSource,
          target: newTarget,
        },
      ];
    },

    clearInterConnection() {
      this.inter_residues = [];
    },

    /// === Import / Export Model Actions === //

    importConfig() {
      this.$refs.importInput.click();
    },

    readJsonFile(event) {
      const file = event.target.files[0];
      if (file && file.size > JSON_MAX_UPLOAD_SIZE) {
        alert("JSON file upload size exceeds the maximum limit.");
        event.target.value = "";
        return;
      }
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => this.createJsonPreview(e.target.result);
      reader.readAsText(file);
      event.target.value = "";
    },

    createJsonPreview(jsonStr) {
      try {
        if (jsonStr.length > JSON_MAX_CHARS) {
          alert("JSON data is too large");
          return;
        }
        const json = JSON.parse(jsonStr);
        const importedData = JsonBuilder.buildJsonFromFile(json);

        this.modelName = importedData.name;
        this.modelDescription = importedData.description;
        this.beads = importedData.beads;
        this.intra_residues = importedData.intra_residues;
        this.inter_residues = importedData.inter_residues;
      } catch (error) {
        alert("Invalid JSON data");
        console.error("JSON Parse Error:", error);
      }
    },

    updateJsonPreview(){
      jsonStr = JSON.stringify(JsonBuilder.buildJsonFromState(this), null, 2)
      if (this.getJsonChars() > JSON_MAX_CHARS){
        return "JSON data is too large.";
      }
      return jsonStr;
    },

    downloadConfig() {
      const json = JsonBuilder.buildJsonFromState(this);
      JsonBuilder.downloadConfig(json, this.modelName);
    },

    applyModel() {
      const json = JsonBuilder.buildJsonFromState(this);
      Alpine.store("modelSelection").sendConfigToForm(json);
    },
  }));
});
