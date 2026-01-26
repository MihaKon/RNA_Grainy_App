document.addEventListener("alpine:init", () => {
    Alpine.store("modelSelection", {
        customJson: "",
        selectedId: "",
        selectedLabel: "Select model",
        sendConfigToForm(json) {
            this.customJson = JSON.stringify(json, null, 2);
            this.selectedId = "custom";
            this.selectedLabel = json.model_name || "Custom Model";
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