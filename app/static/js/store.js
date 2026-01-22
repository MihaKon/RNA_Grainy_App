document.addEventListener("alpine:init", () => {
    Alpine.store("modelSelection", {
        selectedId: "",
        selectedLabel: "Select model",
        customJson: "",

        setCustom() {
            this.selectedId = "custom";
            this.selectedLabel = "Custom Model";
        },

        loadData(json) {
            this.customJson = json;
            this.setCustom(); 
        }
    });
});