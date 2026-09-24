import { describe, expect, it } from "vitest";

import { appConfig } from "@/test/fixtures";

import { readCustomModelFile } from "./customModel";

const jsonFile = (content: string) => new File([content], "model.json");

describe("readCustomModelFile", () => {
  it("reads the model name and keeps the raw JSON", async () => {
    const json = JSON.stringify({ model_name: "<b>My model</b>", mapping: [] });

    await expect(readCustomModelFile(jsonFile(json), appConfig)).resolves.toEqual({
      fileName: "model.json",
      name: "<b>My model</b>",
      json,
    });
  });

  it("falls back to a default name", async () => {
    const model = await readCustomModelFile(
      jsonFile('{"model_name": "  "}'),
      appConfig,
    );
    expect(model.name).toBe("Custom Model");
  });

  it.each([
    ["{not json", "The file is not valid JSON."],
    ["[1, 2]", "The model definition must be a JSON object."],
    ["null", "The model definition must be a JSON object."],
  ])("rejects %s", async (content, message) => {
    await expect(readCustomModelFile(jsonFile(content), appConfig)).rejects.toThrow(
      message,
    );
  });

  it("enforces the size and length limits", async () => {
    const content = JSON.stringify({ description: "x".repeat(20) });

    await expect(
      readCustomModelFile(jsonFile(content), {
        ...appConfig,
        custom_model_json_max_size: 10,
      }),
    ).rejects.toThrow("The file exceeds the 10 B limit.");
    await expect(
      readCustomModelFile(jsonFile(content), {
        ...appConfig,
        custom_model_json_max_chars: 10,
      }),
    ).rejects.toThrow("The model definition exceeds 10 characters.");
  });
});
