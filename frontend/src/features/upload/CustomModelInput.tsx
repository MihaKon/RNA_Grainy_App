import { FileJson, X } from "lucide-react";
import { type ChangeEvent, useRef, useState } from "react";

import type { AppConfig } from "@/api/types";
import { Button } from "@/components/ui/Button";

import {
  CustomModelFileError,
  type LoadedCustomModel,
  readCustomModelFile,
} from "./customModel";

interface CustomModelInputProps {
  config: AppConfig;
  value: LoadedCustomModel | null;
  onChange: (model: LoadedCustomModel | null) => void;
}

export function CustomModelInput({ config, value, onChange }: CustomModelInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [readError, setReadError] = useState<string | null>(null);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    try {
      onChange(await readCustomModelFile(file, config));
      setReadError(null);
    } catch (error) {
      setReadError(
        error instanceof CustomModelFileError
          ? error.message
          : "Could not read the file.",
      );
    }
  };

  return (
    <div className="flex flex-col gap-2 rounded border border-dashed border-line-soft p-4">
      <input
        ref={inputRef}
        type="file"
        accept=".json,application/json"
        aria-label="Custom model JSON file"
        onChange={(event) => void handleFileChange(event)}
        className="sr-only"
        tabIndex={-1}
      />

      {value ? (
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="eyebrow">Custom model loaded</p>
            <p className="truncate text-sm font-medium text-ink">{value.name}</p>
            <p className="truncate font-mono text-label text-ink-3">{value.fileName}</p>
          </div>
          <button
            type="button"
            onClick={() => {
              onChange(null);
            }}
            aria-label="Remove custom model"
            className="rounded p-1.5 text-ink-3 transition-colors hover:text-red-deep"
          >
            <X className="size-4" />
          </button>
        </div>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-ink-2">
            Load a model definition exported as JSON.
          </p>
          <Button
            variant="ghost"
            onClick={() => {
              inputRef.current?.click();
            }}
          >
            <FileJson aria-hidden="true" className="size-4" />
            Load JSON
          </Button>
        </div>
      )}

      {readError && (
        <p role="alert" className="text-xs text-red-deep">
          {readError}
        </p>
      )}
    </div>
  );
}
