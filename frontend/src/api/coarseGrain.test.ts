import { describe, expect, it } from "vitest";

import { coarseGrainResult } from "@/test/fixtures";
import { jsonResponse, mockFetch, requestBody } from "@/test/fetchMock";

import { coarseGrain } from "./coarseGrain";

describe("coarseGrain", () => {
  it("posts an uploaded file with trimmed options", async () => {
    const fetchMock = mockFetch({
      "POST /api/coarse-grain/file": () => jsonResponse(coarseGrainResult),
    });
    const file = new File(["ATOM"], "structure.pdb");

    const result = await coarseGrain({
      source: { kind: "file", file },
      modelId: "SimModel",
      models: " 1, 2 ",
      chains: "",
    });

    expect(result).toEqual(coarseGrainResult);
    const body = requestBody(fetchMock, "/api/coarse-grain/file");
    expect(body.get("file")).toBeInstanceOf(File);
    expect(body.get("selected_model")).toBe("SimModel");
    expect(body.get("models")).toBe("1, 2");
    expect(body.has("chains")).toBe(false);
    expect(body.has("custom_model_data")).toBe(false);
  });

  it.each([
    [{ kind: "rcsb", rcsbId: "1EHZ" }, "/api/coarse-grain/rcsb", "rcsb_id", "1EHZ"],
    [
      { kind: "preset", presetId: "2F8S" },
      "/api/coarse-grain/preset",
      "preset_id",
      "2F8S",
    ],
  ] as const)("posts %o to %s", async (source, url, field, value) => {
    const fetchMock = mockFetch({
      [`POST ${url}`]: () => jsonResponse(coarseGrainResult),
    });

    await coarseGrain({ source, modelId: "custom", customModelJson: "{}" });

    const body = requestBody(fetchMock, url);
    expect(body.get(field)).toBe(value);
    expect(body.get("custom_model_data")).toBe("{}");
  });
});
