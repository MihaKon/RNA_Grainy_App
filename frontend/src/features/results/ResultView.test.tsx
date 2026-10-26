import { act, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ResultStructures } from "@/api/results";
import { jsonResponse, mockFetch } from "@/test/fetchMock";
import { coarseGrainResult } from "@/test/fixtures";
import { renderApp } from "@/test/renderApp";

import { StructureViewer } from "./viewer/StructureViewer";

vi.mock("./viewer/StructureViewer", () => ({
  StructureViewer: vi.fn(({ structures }: { structures: ResultStructures }) => (
    <p>Viewer showing {structures.reference}</p>
  )),
}));

const { files } = coarseGrainResult;

function mockResultFiles() {
  return mockFetch({
    [`GET ${files.reference_url}`]: () => new Response("reference"),
    [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
    [`GET ${files.coarse_pdb_url ?? ""}`]: () => new Response("coarse pdb"),
  });
}

function renderResult(result = coarseGrainResult) {
  return renderApp({
    pathname: `/results/${result.workspace_id}`,
    state: { result },
  });
}

const createObjectURL = vi.fn(() => "blob:result");

describe("ResultView", () => {
  beforeEach(() => {
    vi.mocked(StructureViewer).mockImplementation(({ structures }) => (
      <p>Viewer showing {structures.reference}</p>
    ));
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows the conversion summary and the loaded structures", async () => {
    mockResultFiles();
    renderResult();

    expect(await screen.findByText("Viewer showing reference")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/^1EHZ$/);
    expect(screen.queryByText(/Job/)).not.toBeInTheDocument();
    const report = screen.getByRole("region", { name: "Conversion summary" });
    expect(
      within(report)
        .getAllByRole("term")
        .map((term) => term.textContent),
    ).toEqual([
      "CG model",
      "CG resolution",
      "Input models",
      "Input chains",
      "Input atoms",
      "CG beads",
      "Atom reduction",
    ]);
    expect(within(report).getByText("5 beads per nucleotide")).toBeInTheDocument();
    expect(within(report).getByText("1,821")).toBeInTheDocument();
    expect(within(report).getByText("310")).toBeInTheDocument();
    expect(within(report).getByText("82.98%")).toBeInTheDocument();
  });

  it("shares the current result from the results page", async () => {
    mockResultFiles();
    const { user } = renderResult();
    const writeText = vi
      .spyOn(navigator.clipboard, "writeText")
      .mockResolvedValue(undefined);

    await user.click(await screen.findByRole("button", { name: "Share results" }));

    expect(writeText).toHaveBeenCalledExactlyOnceWith(
      `${window.location.origin}/results/${coarseGrainResult.workspace_id}/`,
    );
    expect(await screen.findByRole("button", { name: "Link copied" })).toBeEnabled();
    expect(screen.getByRole("group", { name: "Download CG model" })).toBeVisible();
    expect(screen.getByText("Result link copied to clipboard.")).toHaveAttribute(
      "role",
      "status",
    );
  });

  it("provides a selectable result link when clipboard access is denied", async () => {
    mockResultFiles();
    const { user } = renderResult();
    vi.spyOn(navigator.clipboard, "writeText").mockRejectedValue(
      new DOMException("Clipboard denied", "NotAllowedError"),
    );

    await user.click(await screen.findByRole("button", { name: "Share results" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not copy automatically",
    );
    const input = screen.getByRole<HTMLInputElement>("textbox", {
      name: "Result link",
    });
    const url = `${window.location.origin}/results/${coarseGrainResult.workspace_id}/`;
    expect(input).toHaveValue(url);
    expect(input).toHaveAttribute("readonly");

    await user.tab();

    expect(input).toHaveFocus();
    expect(input.selectionStart).toBe(0);
    expect(input.selectionEnd).toBe(url.length);
    expect(
      screen.queryByRole("button", { name: "Link copied" }),
    ).not.toBeInTheDocument();
  });

  it("provides the result link when the Clipboard API is unavailable", async () => {
    mockResultFiles();
    const { user } = renderResult();
    const descriptor = Object.getOwnPropertyDescriptor(navigator, "clipboard");
    Reflect.deleteProperty(navigator, "clipboard");

    try {
      await user.click(await screen.findByRole("button", { name: "Share results" }));

      expect(await screen.findByRole("alert")).toHaveTextContent(
        "Could not copy automatically",
      );
      expect(screen.getByRole("textbox", { name: "Result link" })).toHaveValue(
        `${window.location.origin}/results/${coarseGrainResult.workspace_id}/`,
      );
    } finally {
      if (descriptor) {
        Object.defineProperty(navigator, "clipboard", descriptor);
      }
    }
  });

  it("keeps the summary and downloads available when the viewer fails", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    vi.mocked(StructureViewer).mockImplementation(() => {
      throw new TypeError("Failed to fetch dynamically imported module");
    });
    mockResultFiles();
    const { user } = renderResult();
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The structure viewer could not be loaded.");
    expect(screen.getByRole("region", { name: "Conversion summary" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Reload page" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "PDB" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "mmCIF" })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: "mmCIF" }));
    expect(click).toHaveBeenCalledOnce();
    const anchor = click.mock.contexts[0] as HTMLAnchorElement;
    expect(anchor.download).toBe("1EHZ_SimRNA.cif");
  });

  it("downloads the coarse-grained structure once it is loaded", async () => {
    mockResultFiles();
    const { user } = renderResult();
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);

    const downloads = screen.getByRole("group", { name: "Download CG model" });
    const downloadButton = within(downloads).getByRole("button", { name: "PDB" });
    expect(downloadButton).toBeDisabled();
    await screen.findByText("Viewer showing reference");
    await user.click(downloadButton);

    expect(click).toHaveBeenCalledOnce();
    const anchor = click.mock.contexts[0] as HTMLAnchorElement;
    expect(anchor.download).toBe("1EHZ_SimRNA.pdb");
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
  });

  it("offers only mmCIF when the PDB file is unavailable", async () => {
    mockResultFiles();
    const { user } = renderResult({
      ...coarseGrainResult,
      files: { ...files, coarse_pdb_url: null },
    });
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);

    expect(await screen.findByText("Viewer showing reference")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "PDB" })).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "PDB output is unavailable for structures with 100,000 or more atoms; use mmCIF instead.",
      ),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "mmCIF" }));

    const anchor = click.mock.contexts[0] as HTMLAnchorElement;
    expect(anchor.download).toBe("1EHZ_SimRNA.cif");
  });

  it("shows the result and disables the PDB download when only the PDB file fails", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => undefined);
    mockFetch({
      [`GET ${files.reference_url}`]: () => new Response("reference"),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`GET ${files.coarse_pdb_url ?? ""}`]: () =>
        jsonResponse({ detail: "Server error." }, 500),
    });
    renderResult();

    expect(await screen.findByText("Viewer showing reference")).toBeInTheDocument();
    const pdbButton = screen.getByRole("button", { name: "PDB" });
    expect(pdbButton).toBeDisabled();
    expect(pdbButton).toHaveAccessibleDescription(
      "The PDB file could not be downloaded; use mmCIF instead.",
    );
    expect(screen.getByRole("button", { name: "mmCIF" })).toBeEnabled();
    expect(screen.queryByText(/Chain names in PDB files/)).not.toBeInTheDocument();
  });

  it("links citation markers in the CG model details", async () => {
    mockResultFiles();
    const { user } = renderResult();

    await user.click(screen.getByText("CG model details"));

    expect(screen.getByRole("link", { name: "[1]" })).toHaveAttribute(
      "href",
      "https://doi.org/10.1093/nar/gkv1479",
    );
  });

  it("explains when the result files have expired", async () => {
    mockFetch({
      [`GET ${files.reference_url}`]: () =>
        jsonResponse({ detail: "Requested file does not exist or has expired." }, 404),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`GET ${files.coarse_pdb_url ?? ""}`]: () => new Response("coarse pdb"),
    });
    renderResult();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("This result has expired.");
    expect(alert).toHaveTextContent("kept for 24 hours");
    expect(screen.getByRole("button", { name: "mmCIF" })).toBeDisabled();
  });

  it("shows the server message when the result files cannot be loaded", async () => {
    mockFetch({
      [`GET ${files.reference_url}`]: () =>
        jsonResponse({ detail: "Invalid workspace ID format." }, 422),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`GET ${files.coarse_pdb_url ?? ""}`]: () => new Response("coarse pdb"),
    });
    renderResult();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The result could not be loaded.");
    expect(alert).toHaveTextContent("Invalid workspace ID format.");
  });

  it("keeps the loaded files after leaving the result page", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const fetchMock = mockResultFiles();
    const { router, user } = renderResult();
    await screen.findByText("Viewer showing reference");

    await user.click(screen.getByRole("link", { name: /Process another structure/ }));
    await act(() => vi.advanceTimersByTimeAsync(10 * 60 * 1000));
    await act(() => router.navigate(-1));

    expect(await screen.findByText("Viewer showing reference")).toBeInTheDocument();
    const referenceFetches = fetchMock.mock.calls.filter(
      ([url]) => url === files.reference_url,
    );
    expect(referenceFetches).toHaveLength(1);
  });
});
