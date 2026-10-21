import { act, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ResultStructures } from "@/api/results";
import { jsonResponse, mockFetch } from "@/test/fetchMock";
import { coarseGrainResult } from "@/test/fixtures";
import { renderApp } from "@/test/renderApp";

vi.mock("./viewer/StructureViewer", () => ({
  StructureViewer: ({ structures }: { structures: ResultStructures }) => (
    <p>Viewer showing {structures.reference}</p>
  ),
}));

const { files } = coarseGrainResult;

function mockResultFiles() {
  return mockFetch({
    [`GET ${files.reference_url}`]: () => new Response("reference"),
    [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
    [`GET ${files.coarse_pdb_url ?? ""}`]: () => new Response("coarse pdb"),
    [`POST ${files.consumed_url}`]: () => new Response(null, { status: 204 }),
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
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows the model report and the loaded structures", async () => {
    mockResultFiles();
    renderResult();

    expect(await screen.findByText("Viewer showing reference")).toBeInTheDocument();
    const report = screen.getByRole("region", { name: "Conversion summary" });
    expect(within(report).getByText("1,821")).toBeInTheDocument();
    expect(within(report).getByText("310")).toBeInTheDocument();
    expect(within(report).getByText("82.98%")).toBeInTheDocument();
  });

  it("downloads the coarse-grained structure once it is loaded", async () => {
    mockResultFiles();
    const { user } = renderResult();
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);

    const downloadButton = screen.getByRole("button", { name: "Download PDB" });
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
    expect(
      screen.queryByRole("button", { name: "Download PDB" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "PDB output is unavailable for structures with 100,000 or more atoms.",
      ),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Download mmCIF" }));

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
      [`POST ${files.consumed_url}`]: () => new Response(null, { status: 204 }),
    });
    renderResult();

    expect(await screen.findByText("Viewer showing reference")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download PDB" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Download mmCIF" })).toBeEnabled();
    expect(
      screen.getByText(
        "The PDB file could not be downloaded. The mmCIF file is still available.",
      ),
    ).toBeInTheDocument();
  });

  it("links citation markers in the model description", async () => {
    mockResultFiles();
    const { user } = renderResult();

    await user.click(screen.getByText("Model description"));

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
    expect(alert).toHaveTextContent("kept for about an hour");
    expect(screen.getByRole("button", { name: "Download mmCIF" })).toBeDisabled();
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

    await user.click(screen.getByRole("link", { name: /New structure/ }));
    await act(() => vi.advanceTimersByTimeAsync(10 * 60 * 1000));
    await act(() => router.navigate(-1));

    expect(await screen.findByText("Viewer showing reference")).toBeInTheDocument();
    const referenceFetches = fetchMock.mock.calls.filter(
      ([url]) => url === files.reference_url,
    );
    expect(referenceFetches).toHaveLength(1);
  });
});
