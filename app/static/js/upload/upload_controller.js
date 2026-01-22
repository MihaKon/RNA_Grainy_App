document.addEventListener("alpine:init", () => {
  Alpine.data("uploadForm", () => ({
    file: null,
    rcsbId: "",
    exampleId: "",
    selectedModel: "",
    selectedLabel: "Select model",
    dropdownOpen: false,
    errors: { file: false, model: false },
    isSubmitting: false,
    openUp: false,
    customModelLoaded: false,

    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        this.file = file;
        this.rcsbId = "";
        this.errors.file = false;
      }
    },

    removeFile() {
      this.file = null;
      this.$refs.fileInput.value = "";
    },

    handleRcsbInput() {
      if (this.rcsbId.trim() !== "") {
        this.removeFile();
        this.exampleId = "";
        this.errors.file = false;
      }
    },

    setExample(id) {
      this.exampleId = id;
      this.rcsbId = "";
      this.removeFile();
      this.errors.file = false;

      if (!this.selectedModel) {
        event.stopPropagation();
        this.dropdownOpen = true;
      } else {
        this.$nextTick(() => {
          this.$root.requestSubmit();
        });
      }
    },

    selectModel(id, name) {
      this.selectedModel = id;
      this.selectedLabel = name;
      this.errors.model = false;
      this.dropdownOpen = false;

      if (id !== "custom") {
        this.customModelLoaded = false;
        this.$refs.customModelInput.value = "";
      }

      if (this.exampleId) {
        this.$nextTick(() => {
          this.$root.requestSubmit();
        });
      }
    },

    loadCustomJsonFromFile(event) {
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const json = JSON.parse(e.target.result);
          this.$refs.customModelInput.value = JSON.stringify(json);
          this.customModelLoaded = true;
          this.errors.model = false;
        } catch (error) {
          alert("Invalid JSON file");
          console.error(error);
        }
      };
      reader.readAsText(file);
    },

    loadCustomJsonFromString(jsonStr) {
      try {
        const json = JSON.parse(jsonStr);
        this.$refs.customModelInput.value = JSON.stringify(json);
        this.customModelLoaded = true;
        this.errors.model = false;
      } catch (error) {
        alert("Invalid JSON data");
        console.error(error);
      }
      this.showCreator = false;
    },

    handleApplyModel(jsonStr) {
      this.loadCustomJsonFromString(jsonStr);
    },

    validate() {
      const hasFile = !!this.file;
      const hasRcsb = this.rcsbId.trim().length > 0;
      const hasExample = this.exampleId != "";
      const hasModel = !!this.selectedModel;

      const customModelValid =
        this.selectedModel !== "custom" ||
        this.$refs.customModelInput.value !== "";

      this.errors.file = !hasFile && !hasRcsb && !hasExample;
      this.errors.model = !hasModel || !customModelValid;

      return !this.errors.file && !this.errors.model;
    },

    submitForm(event) {
      if (!this.validate()) {
        event.preventDefault();
        return;
      }
      this.isSubmitting = true;

      if (this.rcsbId.trim() !== "") {
        event.detail.path = "/upload/rcsb/";
      } else if (this.exampleId !== "") {
        event.detail.path = "/upload/example/";
      } else {
        event.detail.path = "/upload/file/";
      }
    },

    checkPosition() {
      const buttonRect = this.$refs.dropdownButton.getBoundingClientRect();
      const spaceBelow = window.innerHeight - buttonRect.bottom;
      this.openUp = spaceBelow < 250;
    },
  }));
});
