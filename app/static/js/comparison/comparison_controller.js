(() => {
  let molstarController = null;
  let activeBlobUrls = [];

  function revokeBlobUrls() {
    for (const blobUrl of activeBlobUrls) {
      URL.revokeObjectURL(blobUrl);
    }

    activeBlobUrls = [];
  }

  async function fetchResultBlob(url) {
    const response = await fetch(url, {
      method: "GET",
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error(
        `Could not download result from ${url}: HTTP ${response.status}`,
      );
    }

    return response.blob();
  }

  function createTrackedBlobUrl(blob) {
    const blobUrl = URL.createObjectURL(blob);
    activeBlobUrls.push(blobUrl);
    return blobUrl;
  }

  function configureDownloadButton(buttonId, blobUrl, label) {
    const button = document.getElementById(buttonId);

    if (!button) {
      return;
    }

    button.href = blobUrl;
    button.textContent = label;

    button.classList.remove("bg-tertiary", "cursor-not-allowed");

    button.classList.add("bg-primary", "hover:bg-secondary");
  }

  async function confirmResultConsumption(url) {
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error(
        `Could not confirm result consumption: HTTP ${response.status}`,
      );
    }
  }

  function getComparisonConfig(container) {
    return {
      referenceUrl: container.dataset.referenceUrl,
      coarseCifUrl: container.dataset.coarseCifUrl,
      coarsePdbUrl: container.dataset.coarsePdbUrl || null,
      consumedUrl: container.dataset.consumedUrl,
      referenceFormat: container.dataset.referenceFormat,
      coarseFormat: container.dataset.coarseFormat,
      isPdbAvailable: container.dataset.pdbAvailable === "true",
    };
  }

  function configureVisibilityButton(buttonId, controller, structureId) {
    const button = document.getElementById(buttonId);

    if (!button) {
      return;
    }

    let visible = controller.isStructureVisible(structureId);

    button.setAttribute("aria-pressed", String(visible));

    button.addEventListener("click", () => {
      visible = !visible;

      controller.setStructureVisibility(
        structureId,
        visible,
      );

      button.setAttribute(
        "aria-pressed",
        String(visible),
      );
    });
  }

  function setActiveRepresentationButton(activeButtonId) {
    const representationButtonIds = [
      "b-and-s",
      "cartoon",
      "backbone",
    ];

    for (const buttonId of representationButtonIds) {
      const button = document.getElementById(buttonId);

      if(button){
        button.setAttribute(
          "aria-pressed",
          String(buttonId === activeButtonId),
        );
      }
    }
  }

  function configureRepresentationButton(buttonId, controller, representationType,
  ) {
    const button = document.getElementById(buttonId);

    if (!button) {
      return;
    }

    button.addEventListener("click", async () => {
      try {
        await controller.setStructureRepresentation(
          "reference",
          representationType,
        );

        await controller.setStructureRepresentation(
          "coarse",
          representationType,
        );

        setActiveRepresentationButton(buttonId);

      } catch (error) {
        console.error(
          "Could not change Mol* representation:",
          error,
        );
      }
    });
  }

  function configureColoringButton(buttonId, controller, structureId) {
    const button = document.getElementById(buttonId);

    if (!button) {
      return;
    }

    function isElementColoringActive() {
      return (
        controller.getStructureColoring(structureId) ===
        "element-symbol"
      );
    }

    button.setAttribute(
      "aria-pressed",
      String(isElementColoringActive()),
    );

    button.addEventListener("click", async () => {
      const nextColorMode = isElementColoringActive()
        ? "uniform"
        : "element-symbol";

      button.disabled = true;

      try {
        await controller.setStructureColoring(
          structureId,
          nextColorMode,
        );

        button.setAttribute(
          "aria-pressed",
          String(isElementColoringActive()),
        );
      } catch (error) {
        console.error(
          "Could not change Mol* coloring:",
          error,
        );
      } finally {
        button.disabled = false;
      }
    });
  }

  function configureVisualizationControls(controller) {
    configureVisibilityButton(
      "vis-cg",
      controller,
      "coarse",
    );

    configureVisibilityButton(
      "vis-aa",
      controller,
      "reference",
    );

    configureRepresentationButton(
      "b-and-s",
      controller,
      "ball-and-stick",
    );

    configureRepresentationButton(
      "cartoon",
      controller,
      "cartoon",
    );

    configureRepresentationButton(
      "backbone",
      controller,
      "backbone",
    );

    configureColoringButton(
      "color-by-element",
      controller,
      "reference",
    );

    setActiveRepresentationButton("b-and-s");

  }

  async function initializeComparison(container) {
    if (container.dataset.initialized === "true") {
      return;
    }

    const config = getComparisonConfig(container);

    const coarsePdbPromise =
      config.isPdbAvailable && config.coarsePdbUrl
        ? fetchResultBlob(config.coarsePdbUrl)
        : Promise.resolve(null);

    const [referenceBlob, coarseCifBlob, coarsePdbBlob] = await Promise.all([
      fetchResultBlob(config.referenceUrl),
      fetchResultBlob(config.coarseCifUrl),
      coarsePdbPromise,
    ]);

    const referenceBlobUrl = createTrackedBlobUrl(referenceBlob);

    const coarseCifBlobUrl = createTrackedBlobUrl(coarseCifBlob);

    const coarsePdbBlobUrl = coarsePdbBlob
      ? createTrackedBlobUrl(coarsePdbBlob)
      : null;

    configureDownloadButton("download-cif", coarseCifBlobUrl, "CIF");

    if (coarsePdbBlobUrl) {
      configureDownloadButton("download-pdb", coarsePdbBlobUrl, "PDB");
    }

    molstarController = await window.createMolstarViewer("molstar-container", [
      {
        id: "reference",
        url: referenceBlobUrl,
        format: config.referenceFormat,
        isCoarse: false,
      },
      {
        id: "coarse",
        url: coarseCifBlobUrl,
        format: config.coarseFormat,
        isCoarse: true,
      },
    ]);

    configureVisualizationControls(molstarController);

    try {
      await confirmResultConsumption(config.consumedUrl);
    } catch (error) {
      console.warn(
        "Result was loaded, but server cleanup confirmation failed.",
        error,
      );
    }

    container.dataset.initialized = "true";
  }

  function startComparisonIfPresent() {
    const container = document.getElementById("comparison-view");

    if (!container) {
      return;
    }

    initializeComparison(container).catch((error) => {
      console.error("Could not initialize comparison:", error);

      const errorElement = document.getElementById("comparison-loading-error");
      const molDiv = document.getElementById("mol-div")

      if (errorElement) {
        errorElement.classList.remove("hidden");
      }
      if (molDiv){
        molDiv.classList.remove("flex");
        molDiv.classList.add("hidden");
      }
    });
  }


  document.body.addEventListener("htmx:afterSwap", startComparisonIfPresent);

  window.addEventListener("pagehide", () => {
    revokeBlobUrls();
    molstarController?.dispose();
    molstarController = null;
  });

})();
