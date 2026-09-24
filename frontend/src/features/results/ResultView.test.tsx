import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ResultStructures } from "@/api/results";
import { coarseGrainResult } from "@/test/fixtures";
import { jsonResponse, mockFetch } from "@/test/fetchMock";
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

function renderResult() {
  return renderApp({
    pathname: `/results/${coarseGrainResult.workspace_id}`,
    state: { result: coarseGrainResult },
  });
}

const createObjectURL = vi.fn(() => "blob:result");

describe("ResultView", () => {
  beforeEach(() => {
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = vi.fn();
  });

  it("shows the model report and the loaded structures", async () => {
    mockResultFiles();
    renderResult();

    expect(await screen.findByText("Viewer showing reference")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/^1EHZ$/);
    expect(screen.queryByText(/Job/)).not.toBeInTheDocument();
    const report = screen.getByRole("region", { name: "Model report" });
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

  it("offers only mmCIF for structures without PDB output", async () => {
    mockResultFiles();
    renderApp({
      pathname: `/results/${coarseGrainResult.workspace_id}`,
      state: {
        result: {
          ...coarseGrainResult,
          files: { ...coarseGrainResult.files, coarse_pdb_url: null },
        },
      },
    });

    await screen.findByText("Viewer showing reference");
    expect(
      screen.queryByRole("button", { name: "Download PDB" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download mmCIF" })).toBeEnabled();
    expect(screen.getByText(/PDB output is unavailable/)).toBeInTheDocument();
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

  it("explains when the result files are gone", async () => {
    mockFetch({
      [`GET ${files.reference_url}`]: () =>
        jsonResponse({ detail: "Workspace not found." }, 422),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`GET ${files.coarse_pdb_url ?? ""}`]: () => new Response("coarse pdb"),
    });
    renderResult();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The result could not be loaded.",
    );
    expect(screen.getByRole("button", { name: "Download mmCIF" })).toBeDisabled();
  });
});
