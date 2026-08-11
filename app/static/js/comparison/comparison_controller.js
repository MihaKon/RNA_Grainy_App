(() => {
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

  async function initializeComparison(container) {
    if (container.dataset.initialized === "true") {
      return;
    }

    container.dataset.initialized = "true";

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

    await window.createMolstarViewer("molstar-container", [
      {
        url: referenceBlobUrl,
        format: config.referenceFormat,
        isCoarse: false,
      },
      {
        url: coarseCifBlobUrl,
        format: config.coarseFormat,
        isCoarse: true,
      },
    ]);

    try {
      await confirmResultConsumption(config.consumedUrl);
    } catch (error) {
      console.warn(
        "Result was loaded, but server cleanup confirmation failed.",
        error,
      );
    }
  }

  function startComparisonIfPresent() {
    const container = document.getElementById("comparison-view");

    if (!container) {
      return;
    }

    initializeComparison(container).catch((error) => {
      console.error("Could not initialize comparison:", error);

      const errorElement = document.getElementById("comparison-loading-error");

      if (errorElement) {
        errorElement.classList.remove("hidden");
      }
    });
  }

  document.body.addEventListener("htmx:afterSwap", startComparisonIfPresent);

  window.addEventListener("pagehide", revokeBlobUrls);
})();
