import { describe, expect, it, vi } from "vitest";

import { coarseGrainResult } from "@/test/fixtures";
import { mockFetch } from "@/test/fetchMock";

import { fetchResultStructures } from "./results";

const { files } = coarseGrainResult;

describe("fetchResultStructures", () => {
  it("downloads every structure before marking the result as consumed", async () => {
    const fetchMock = mockFetch({
      [`GET ${files.reference_url}`]: () => new Response("reference"),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`GET ${files.coarse_pdb_url ?? ""}`]: () => new Response("coarse pdb"),
      [`POST ${files.consumed_url}`]: () => new Response(null, { status: 204 }),
    });

    await expect(fetchResultStructures(files)).resolves.toEqual({
      reference: "reference",
      coarseMmcif: "coarse mmcif",
      coarsePdb: "coarse pdb",
    });
    expect(fetchMock.mock.calls.at(-1)?.[0]).toBe(files.consumed_url);
  });

  it("skips the PDB file when it is unavailable and tolerates cleanup failures", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    mockFetch({
      [`GET ${files.reference_url}`]: () => new Response("reference"),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`POST ${files.consumed_url}`]: () => new Response(null, { status: 500 }),
    });

    const structures = await fetchResultStructures({ ...files, coarse_pdb_url: null });

    expect(structures.coarsePdb).toBeNull();
    expect(warn).toHaveBeenCalledOnce();
  });

  it("fails when a structure cannot be downloaded", async () => {
    mockFetch({
      [`GET ${files.reference_url}`]: () =>
        Response.json({ detail: "Workspace not found." }, { status: 422 }),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`GET ${files.coarse_pdb_url ?? ""}`]: () => new Response("coarse pdb"),
    });

    await expect(fetchResultStructures(files)).rejects.toThrow("Workspace not found.");
  });
});
