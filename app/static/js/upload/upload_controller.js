document.addEventListener("alpine:init", () => {
  Alpine.data("uploadForm", () => ({
    init() {
      this.$watch("$store.modelSelection.selectedId", (id) => {
        this.selectedModel = id;
      });

      this.$watch("$store.modelSelection.selectedLabel", (label) => {
        this.selectedLabel = label;
      });

      this.$watch('rcsbId', (value) => {
        if (value && value.trim().length > 0) {
            this.removeFile(); 
            this.exampleId = ""; 
            this.errors.file = false;
        }
    });
      this.$watch("$store.modelSelection.customJson", (json) => {
        if (json) {
          this.processJsonToModel(json);
        }
      });
    },
    // === State ===
    file: null,
    rcsbId: "",
    exampleId: "",
    selectedModel: "",
    selectedLabel: "Select model",

    dropdownOpen: false,
    openUp: false,
    isSubmitting: false,
    customModelLoaded: false,

    errors: { file: false, model: false },

    // === Input Handling ===

    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        this.rcsbId = "";
        this.exampleId = "";
        this.file = file;
        this.errors.file = false;
      }
    },

    setExample(id) {
      this.removeFile();
      this.rcsbId = "";
      this.exampleId = id;
      this.errors.file = false;

      if (!this.selectedModel) {
        event.stopPropagation();
        this.dropdownOpen = true;
      } else {
        this.autoSubmit();
      }
    },

    resetInputs() {
      this.removeFile();
      this.rcsbId = "";
      this.exampleId = "";
    },

    removeFile() {
      this.file = null;
      if (this.$refs.fileInput) this.$refs.fileInput.value = "";
    },

    // === Model Handling ===

    selectModel(id, name) {
      this.selectedModel = id;
      this.selectedLabel = name;
      this.errors.model = false;
      this.dropdownOpen = false;

      if (id !== "custom") {
        this.clearCustomModel();
      }

      if (this.exampleId) {
        this.autoSubmit();
      }
    },

    clearCustomModel() {
      this.customModelLoaded = false;
      if (this.$refs.customModelInput) this.$refs.customModelInput.value = "";
    },

    // === JSON Handling ===

    uploadJson(){
      return this.$refs.jsonUpload.click();
    },

    readJsonFile(event) {
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => this.processJsonToModel(e.target.result);
      reader.readAsText(file);
    },

    processJsonToModel(jsonStr) {
      try {
        const json = JSON.parse(jsonStr);
        Alpine.store("modelSelection").sendConfigToForm(json);
        this.$refs.customModelInput.value = jsonStr;
        this.customModelLoaded = true;
        this.errors.model = false;
      } catch (error) {
        alert("Invalid JSON data");
        console.error("JSON Parse Error:", error);
      }
    },

    // === Validation & Submission ===

    validate() {
      const hasInput = !!this.file || !!this.rcsbId.trim() || !!this.exampleId;
      const customValid =
        this.selectedModel !== "custom" ||
        this.$refs.customModelInput.value !== "";
      const hasModel = !!this.selectedModel && customValid;

      this.errors.file = !hasInput;
      this.errors.model = !hasModel;

      return !this.errors.file && !this.errors.model;
    },

    getSubmitPath() {
      if (this.rcsbId) return UPLOAD_ENDPOINTS.RCSB;
      if (this.exampleId) return UPLOAD_ENDPOINTS.EXAMPLE;
      return UPLOAD_ENDPOINTS.FILE;
    },

    submitForm(event) {
      if (!this.validate()) {
        event.preventDefault();
        return;
      }
      this.isSubmitting = true;
      event.detail.path = this.getSubmitPath();
    },

    autoSubmit() {
      this.$nextTick(() => {
        this.$root.requestSubmit();
      });
    },

    // === Dropdown Positioning ===

    checkPosition() {
      const buttonRect = this.$refs.dropdownButton.getBoundingClientRect();
      const spaceBelow = window.innerHeight - buttonRect.bottom;
      this.openUp = spaceBelow < 250;
    },
  }));
});
