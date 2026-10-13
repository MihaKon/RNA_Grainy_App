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
  it("reads every structure in full before marking the result as consumed", async () => {
    const reference = pendingBody("reference");
    const coarseMmcif = pendingBody("coarse mmcif");
    const coarsePdb = pendingBody("coarse pdb");
    const fetchMock = mockFetch({
      [`GET ${files.reference_url}`]: () => reference.response,
      [`GET ${files.coarse_mmcif_url}`]: () => coarseMmcif.response,
      [`GET ${files.coarse_pdb_url ?? ""}`]: () => coarsePdb.response,
      [`POST ${files.consumed_url}`]: () => new Response(null, { status: 204 }),
    });
    const consumedCalls = () =>
      fetchMock.mock.calls.filter(([url]) => url === files.consumed_url);

    const structures = fetchResultStructures(files);
    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });
    reference.finish();
    coarseMmcif.finish();
    await new Promise((resolve) => {
      setTimeout(resolve, 0);
    });
    expect(consumedCalls()).toHaveLength(0);

    coarsePdb.finish();
    await expect(structures).resolves.toEqual({
      reference: "reference",
      coarseMmcif: "coarse mmcif",
      coarsePdb: "coarse pdb",
    });
    expect(consumedCalls()).toHaveLength(1);
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
