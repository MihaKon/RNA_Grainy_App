import { describe, expect, it } from "vitest";

import { appConfig } from "@/test/fixtures";

import {
  toStructureSource,
  type UploadFormValues,
  validateStructureFile,
  validateUploadForm,
} from "./validation";

const validValues: UploadFormValues = {
  sourceKind: "preset",
  file: null,
  rcsbId: "",
  presetId: "1EHZ",
  modelId: "SimModel",
  customModel: null,
  models: "",
  chains: "",
};

describe("validateUploadForm", () => {
  it("accepts a complete form", () => {
    expect(validateUploadForm(validValues, appConfig)).toEqual({});
  });

  it.each([
    [{ sourceKind: "file" }, "Choose a structure file."],
    [{ sourceKind: "rcsb", rcsbId: "" }, "Enter a 4-character PDB ID, e.g. 1EHZ."],
    [{ sourceKind: "rcsb", rcsbId: "1EH" }, "Enter a 4-character PDB ID, e.g. 1EHZ."],
    [{ sourceKind: "preset", presetId: "" }, "Choose an example structure."],
  ] as const)("reports a missing source for %o", (patch, message) => {
    expect(validateUploadForm({ ...validValues, ...patch }, appConfig).source).toBe(
      message,
    );
  });

  it("accepts a PDB ID regardless of case and whitespace", () => {
    const values = { ...validValues, sourceKind: "rcsb", rcsbId: " 1ehz " } as const;
    expect(validateUploadForm(values, appConfig)).toEqual({});
    expect(toStructureSource(values)).toEqual({ kind: "rcsb", rcsbId: "1EHZ" });
  });

  it("requires a model and a loaded custom model definition", () => {
    expect(validateUploadForm({ ...validValues, modelId: "" }, appConfig).model).toBe(
      "Select a coarse-grained model.",
    );
    expect(
      validateUploadForm({ ...validValues, modelId: "custom" }, appConfig).model,
    ).toBe("Load a custom model JSON file.");
  });

  it("validates the model and chain selections", () => {
    const errors = validateUploadForm(
      { ...validValues, models: "1, -2", chains: "A; B" },
      appConfig,
    );

    expect(errors.models).toBe("Use model numbers separated by commas.");
    expect(errors.chains).toBe(
      "Use chain IDs (letters and digits) separated by commas.",
    );
  });
});

describe("validateStructureFile", () => {
  it("accepts supported formats case-insensitively", () => {
    expect(
      validateStructureFile(new File(["x"], "1EHZ.CIF"), appConfig),
    ).toBeUndefined();
  });

  it.each([
    [
      new File(["x"], "structure.txt"),
      "Unsupported file format. Use .pdb, .cif or .mmcif.",
    ],
    [new File(["x"], "pdb"), "Unsupported file format. Use .pdb, .cif or .mmcif."],
    [new File([], "empty.pdb"), "The file is empty."],
  ])("rejects %s", (file, message) => {
    expect(validateStructureFile(file, appConfig)).toBe(message);
  });

  it("rejects files above the upload limit", () => {
    const config = { ...appConfig, max_file_upload_size: 4 };
    expect(validateStructureFile(new File(["ATOM!"], "big.pdb"), config)).toBe(
      "The file exceeds the 4 B limit.",
    );
  });
});
