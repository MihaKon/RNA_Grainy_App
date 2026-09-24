import { type ChangeEvent, useReducer, useRef, useState } from "react";

import type { AppConfig } from "@/api/types";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Disclosure } from "@/components/ui/Disclosure";
import { type TabItem, Tabs } from "@/components/ui/Tabs";
import { TextField } from "@/components/ui/TextField";
import {
  CustomModelFileError,
  type LoadedCustomModel,
  readCustomModelFile,
} from "@/features/upload/customModel";
import { cn } from "@/lib/cn";
import { downloadTextFile } from "@/lib/download";

import { BeadEditor } from "./BeadEditor";
import { ConnectivityEditor } from "./ConnectivityEditor";
import {
  draftReducer,
  fromDefinition,
  type ModelDraft,
  serializeDefinition,
  toDefinition,
  validateDraft,
} from "./modelDraft";

type CreatorTab = "beads" | "connectivity";

const CREATOR_TABS: readonly TabItem<CreatorTab>[] = [
  { value: "beads", label: "Beads" },
  { value: "connectivity", label: "Connectivity" },
];

export const CREATOR_ORIGIN = "Model creator";

interface ModelCreatorProps {
  titleId: string;
  config: AppConfig;
  initialDraft: ModelDraft;
  onApply: (model: LoadedCustomModel) => void;
  onCancel: () => void;
}

export function ModelCreator({
  titleId,
  config,
  initialDraft,
  onApply,
  onCancel,
}: ModelCreatorProps) {
  const [draft, dispatch] = useReducer(draftReducer, initialDraft);
  const [tab, setTab] = useState<CreatorTab>("beads");
  const [importError, setImportError] = useState<string | null>(null);
  const importInputRef = useRef<HTMLInputElement>(null);

  const json = serializeDefinition(toDefinition(draft));
  const issues = validateDraft(draft);
  const maxChars = config.custom_model_json_max_chars;
  const tooLong = json.length > maxChars;
  const issueCount =
    issues.model.length + Object.values(issues.beads).flat().length + (tooLong ? 1 : 0);

  const handleImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    try {
      const model = await readCustomModelFile(file, config);
      dispatch({
        type: "replace",
        draft: fromDefinition(JSON.parse(model.json) as Record<string, unknown>),
      });
      setImportError(null);
    } catch (error) {
      setImportError(
        error instanceof CustomModelFileError
          ? error.message
          : "Could not read the file.",
      );
    }
  };

  const handleExport = () => {
    const fileName =
      draft.name.trim().toLowerCase().replace(/\s+/g, "_") || "custom_model";
    downloadTextFile(json, `${fileName}.json`);
  };

  return (
    <div>
      <header className="z-10 border-b border-line-soft bg-surface lg:sticky lg:top-0">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4 px-4 py-4 lg:px-8">
          <div>
            <p className="eyebrow">Custom model</p>
            <h2 id={titleId} className="font-display text-heading-compact text-ink">
              Model <span className="text-accent">creator</span>
            </h2>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={importInputRef}
              type="file"
              accept=".json,application/json"
              aria-label="Import model JSON file"
              tabIndex={-1}
              className="sr-only"
              onChange={(event) => void handleImport(event)}
            />
            <Button
              variant="ghost"
              onClick={() => {
                importInputRef.current?.click();
              }}
            >
              Import JSON
            </Button>
            <Button variant="ghost" disabled={tooLong} onClick={handleExport}>
              Export JSON
            </Button>
            <Button variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
            <Button
              disabled={issueCount > 0}
              onClick={() => {
                onApply({ name: draft.name.trim(), json, origin: CREATOR_ORIGIN });
              }}
            >
              Use model
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[3fr_2fr] lg:px-8">
        <div className="flex min-w-0 flex-col gap-5">
          {importError && <Alert severity="error">{importError}</Alert>}
          {issueCount > 0 && (
            <Alert severity="info">
              <p>
                Resolve {issueCount} {issueCount === 1 ? "issue" : "issues"} before
                using the model.
              </p>
              {issues.model.length > 0 && (
                <ul className="mt-1 list-disc pl-4">
                  {issues.model.map((issue) => (
                    <li key={issue}>{issue}</li>
                  ))}
                </ul>
              )}
            </Alert>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            <TextField
              label="Model name"
              value={draft.name}
              onChange={(event) => {
                dispatch({ type: "setModelInfo", patch: { name: event.target.value } });
              }}
            />
            <TextField
              label="Description"
              value={draft.description}
              onChange={(event) => {
                dispatch({
                  type: "setModelInfo",
                  patch: { description: event.target.value },
                });
              }}
            />
          </div>

          <div className="overflow-hidden rounded-md border border-line-soft bg-white">
            <Tabs
              label="Model definition"
              items={CREATOR_TABS}
              value={tab}
              onChange={setTab}
              panelClassName="bg-surface p-4 lg:p-5"
            >
              {tab === "beads" ? (
                <div className="flex flex-col gap-4">
                  <Disclosure title="How beads work">
                    <BeadRules />
                  </Disclosure>
                  {draft.beads.map((bead) => (
                    <BeadEditor
                      key={bead.key}
                      bead={bead}
                      issues={issues.beads[bead.key]}
                      dispatch={dispatch}
                    />
                  ))}
                  <Button
                    variant="ghost"
                    className="self-start"
                    onClick={() => {
                      dispatch({ type: "addBead" });
                    }}
                  >
                    Add bead
                  </Button>
                </div>
              ) : (
                <ConnectivityEditor draft={draft} dispatch={dispatch} />
              )}
            </Tabs>
          </div>
        </div>

        <aside aria-labelledby="json-preview-heading" className="min-w-0">
          <div className="flex flex-col gap-2 lg:sticky lg:top-28">
            <div className="flex items-baseline justify-between gap-3">
              <h3 id="json-preview-heading" className="eyebrow">
                JSON preview
              </h3>
              <p
                className={cn(
                  "font-mono text-label",
                  tooLong ? "text-red-deep" : "text-ink-3",
                )}
              >
                {json.length.toLocaleString("en-US")} /{" "}
                {maxChars.toLocaleString("en-US")} characters
              </p>
            </div>
            <pre className="max-h-[70dvh] overflow-auto rounded-md border border-line-soft bg-white p-4 font-mono text-xs text-ink-2">
              {json}
            </pre>
          </div>
        </aside>
      </div>
    </div>
  );
}

function BeadRules() {
  return (
    <div className="flex flex-col gap-3 text-sm text-ink-2">
      <p>
        <strong className="font-medium text-ink">Bead ID</strong> identifies the bead
        when building the structure and defining connections.{" "}
        <strong className="font-medium text-ink">Bead name</strong> becomes the atom
        name shown in the coarse-grained structure.
      </p>
      <p>
        To place a bead on different atoms depending on the residue, add several beads
        with the same ID and different scopes, e.g. one bead{" "}
        <code className="font-mono">A3</code> for purines and another for pyrimidines.
        Connections defined for an ID apply to all beads that share it.
      </p>
    </div>
  );
}
