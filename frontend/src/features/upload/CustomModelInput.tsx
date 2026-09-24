import { FileJson, PencilRuler, X } from "lucide-react";
import { type ChangeEvent, useId, useRef, useState } from "react";

import type { AppConfig } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { Drawer } from "@/components/ui/Drawer";
import { ModelCreator } from "@/features/creator/ModelCreator";
import {
  createDefaultDraft,
  fromDefinition,
  type ModelDraft,
} from "@/features/creator/modelDraft";

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
  const creatorTitleId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [readError, setReadError] = useState<string | null>(null);
  const [creatorDraft, setCreatorDraft] = useState<ModelDraft | null>(null);

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

  const openCreator = () => {
    setCreatorDraft(
      value
        ? fromDefinition(JSON.parse(value.json) as Record<string, unknown>)
        : createDefaultDraft(),
    );
  };

  return (
    <div className="flex flex-col gap-3 rounded border border-dashed border-line-soft p-4">
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
            <p className="truncate font-mono text-label text-ink-3">{value.origin}</p>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <Button variant="ghost" onClick={openCreator}>
              Edit
            </Button>
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
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-ink-2">
            Build a model in the creator or load a definition exported as JSON.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button variant="ghost" onClick={openCreator}>
              <PencilRuler aria-hidden="true" className="size-4" />
              Open creator
            </Button>
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
        </div>
      )}

      {readError && (
        <p role="alert" className="text-xs text-red-deep">
          {readError}
        </p>
      )}

      <Drawer
        open={creatorDraft !== null}
        labelledBy={creatorTitleId}
        onClose={() => {
          setCreatorDraft(null);
        }}
      >
        {creatorDraft && (
          <ModelCreator
            titleId={creatorTitleId}
            config={config}
            initialDraft={creatorDraft}
            onApply={(model) => {
              onChange(model);
              setReadError(null);
              setCreatorDraft(null);
            }}
            onCancel={() => {
              setCreatorDraft(null);
            }}
          />
        )}
      </Drawer>
    </div>
  );
}
