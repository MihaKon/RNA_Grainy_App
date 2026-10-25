import { describe, expect, it, vi } from "vitest";

import { mockFetch } from "@/test/fetchMock";
import { coarseGrainResult } from "@/test/fixtures";

import { fetchResultStructures } from "./results";

const { files } = coarseGrainResult;

function pendingBody(text: string) {
  let finish!: () => void;
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(text));
      finish = () => {
        controller.close();
      };
    },
  });
  return { response: new Response(body), finish };
}

describe("fetchResultStructures", () => {
  it("reads every structure in full using only GET requests", async () => {
    const reference = pendingBody("reference");
    const coarseMmcif = pendingBody("coarse mmcif");
    const coarsePdb = pendingBody("coarse pdb");
    const fetchMock = mockFetch({
      [`GET ${files.reference_url}`]: () => reference.response,
      [`GET ${files.coarse_mmcif_url}`]: () => coarseMmcif.response,
      [`GET ${files.coarse_pdb_url ?? ""}`]: () => coarsePdb.response,
    });
    let resolved = false;
    const structures = fetchResultStructures(files).then((result) => {
      resolved = true;
      return result;
    });
    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });
    reference.finish();
    coarseMmcif.finish();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(resolved).toBe(false);

    coarsePdb.finish();
    await expect(structures).resolves.toEqual({
      reference: "reference",
      coarseMmcif: "coarse mmcif",
      coarsePdb: "coarse pdb",
      coarsePdbFailed: false,
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(
      fetchMock.mock.calls.every(([, init]) => (init?.method ?? "GET") === "GET"),
    ).toBe(true);
  });

  it("skips the PDB file when it is unavailable", async () => {
    const fetchMock = mockFetch({
      [`GET ${files.reference_url}`]: () => new Response("reference"),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
    });

    const structures = await fetchResultStructures({ ...files, coarse_pdb_url: null });

    expect(structures.coarsePdb).toBeNull();
    expect(structures.coarsePdbFailed).toBe(false);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("keeps the required structures when the optional PDB download fails", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const fetchMock = mockFetch({
      [`GET ${files.reference_url}`]: () => new Response("reference"),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`GET ${files.coarse_pdb_url ?? ""}`]: () =>
        Response.json({ detail: "Server error." }, { status: 500 }),
    });

    const structures = await fetchResultStructures(files);

    expect(structures.coarseMmcif).toBe("coarse mmcif");
    expect(structures.coarsePdb).toBeNull();
    expect(structures.coarsePdbFailed).toBe(true);
    expect(warn).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("fails when a required structure cannot be downloaded", async () => {
    mockFetch({
      [`GET ${files.reference_url}`]: () =>
        Response.json({ detail: "Workspace not found." }, { status: 404 }),
      [`GET ${files.coarse_mmcif_url}`]: () => new Response("coarse mmcif"),
      [`GET ${files.coarse_pdb_url ?? ""}`]: () => new Response("coarse pdb"),
    });

    await expect(fetchResultStructures(files)).rejects.toThrow("Workspace not found.");
  });
});
