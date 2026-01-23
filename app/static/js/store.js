document.addEventListener("alpine:init", () => {
    Alpine.store("modelSelection", {
        selectedId: "",
        selectedLabel: "Select model",
        customJson: "",

        loadDataToForm(json) {
            this.customJson = json;
            this.selectedId = "custom";
            this.selectedLabel = "Custom Model";
        }
    });

    Alpine.store("openCreator", {
        isOpen: false,
        
        open() {
            this.isOpen = true;
        },

        close() {
            this.isOpen = false;
        }
    });
});