import { ChevronDown, CircleAlert, CircleCheck } from "lucide-react";
import {
  type ChangeEvent,
  type Dispatch,
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
} from "react";

import type { AppConfig } from "@/api/types";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import {
  CustomModelFileError,
  customModelSizeIssues,
  type LoadedCustomModel,
  readCustomModelFile,
} from "@/features/upload/customModel";
import { useDropdownDismiss } from "@/hooks/useDropdownDismiss";
import { cn } from "@/lib/cn";
import { downloadTextFile } from "@/lib/download";

import { BeadEditor } from "./BeadEditor";
import { CreatorGuide } from "./CreatorGuide";
import {
  createDefaultDraft,
  createEmptyDraft,
  type DraftAction,
  draftReducer,
  fromDefinition,
  type ModelDraft,
  serializeDefinition,
  toDefinition,
  validateDraft,
} from "./modelDraft";
import { MoleculeEditor } from "./MoleculeEditor";

const CreatorPreview = lazy(() => import("./CreatorPreview"));
export const CREATOR_ORIGIN = "Model creator";

interface ModelCreatorProps {
  titleId: string;
  config: AppConfig;
  draft: ModelDraft;
  dispatch: Dispatch<DraftAction>;
  onApply: (model: LoadedCustomModel) => void;
  onCancel: () => void;
}

function restoreEditorFocus(target: HTMLElement | null, panel: HTMLElement | null) {
  if (target?.isConnected) target.focus();
  else
    panel
      ?.closest("dialog")
      ?.querySelector<HTMLButtonElement>('button[aria-label="Bead settings"]')
      ?.focus();
}

export function ModelCreator({
  titleId,
  config,
  draft,
  dispatch,
  onApply,
  onCancel,
}: ModelCreatorProps) {
  const [previewTab, setPreviewTab] = useState<"live" | "json">("live");
  const [importError, setImportError] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const importInputRef = useRef<HTMLInputElement>(null);
  const modelMenuRef = useRef<HTMLDetailsElement>(null);
  const detailsRef = useRef<HTMLDetailsElement>(null);
  const guideRef = useRef<HTMLDetailsElement>(null);
  useDropdownDismiss(detailsRef, () => {
    detailsRef.current?.removeAttribute("open");
  });
  useDropdownDismiss(modelMenuRef, () => {
    modelMenuRef.current?.removeAttribute("open");
  });
  useDropdownDismiss(guideRef, () => {
    guideRef.current?.removeAttribute("open");
  });
  const editorRef = useRef<HTMLElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const active = draft.beads.find((bead) => bead.key === selectedKey) ?? draft.beads[0];
  const json = serializeDefinition(toDefinition(draft));
  const issues = validateDraft(draft);
  const sizeIssues = customModelSizeIssues(json, config);
  const modelIssues = [...issues.model, ...sizeIssues];
  const tooLarge = sizeIssues.length > 0;
  const issueCount = modelIssues.length + Object.values(issues.beads).flat().length;
  const modelStatus = issueCount
    ? `${issueCount.toString()} model ${issueCount === 1 ? "issue" : "issues"}`
    : "Model ready";

  const openEditor = (key?: string) => {
    guideRef.current?.removeAttribute("open");
    returnFocusRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    if (key) setSelectedKey(key);
    setEditorOpen(true);
  };
  const closeEditor = () => {
    setEditorOpen(false);
    restoreEditorFocus(returnFocusRef.current, editorRef.current);
  };

  useEffect(() => {
    if (!editorOpen) return;
    editorRef.current?.focus();
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      setEditorOpen(false);
      restoreEditorFocus(returnFocusRef.current, editorRef.current);
    };
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [editorOpen]);

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
      setEditorOpen(false);
    } catch (error) {
      setImportError(
        error instanceof CustomModelFileError
          ? error.message
          : "Could not read the file.",
      );
    }
  };
  const handleExport = () => {
    const name = draft.name.trim().toLowerCase().replace(/\s+/g, "_") || "custom_model";
    downloadTextFile(json, `${name}.json`);
    modelMenuRef.current?.removeAttribute("open");
  };

  const beadSettings = editorOpen ? (
    <section
      ref={editorRef}
      tabIndex={-1}
      aria-labelledby="bead-settings-heading"
      className="fixed inset-x-4 top-24 z-40 mt-2 flex max-h-[calc(100dvh-7rem)] flex-col overflow-hidden rounded-md border border-line-soft bg-white shadow-xl transition-[transform,opacity] duration-150 outline-none motion-reduce:transition-none min-[640px]:absolute min-[640px]:inset-x-auto min-[640px]:top-full min-[640px]:right-0 min-[640px]:max-h-[min(70dvh,620px)] min-[640px]:w-[360px] starting:-translate-y-2 starting:opacity-0"
    >
      <div className="flex items-center justify-between border-b border-line-soft px-4 py-3">
        <h3 id="bead-settings-heading" className="eyebrow">
          Bead settings
        </h3>
        <Button variant="ghost" aria-label="Close bead settings" onClick={closeEditor}>
          Close
        </Button>
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-4">
        <div>
          {active ? (
            <BeadEditor
              key={active.key}
              draft={draft}
              bead={active}
              issues={issues.beads[active.key]}
              dispatch={dispatch}
            />
          ) : (
            <p className="text-xs text-ink-3">Choose Add bead in the 2D editor.</p>
          )}
        </div>
      </div>
    </section>
  ) : null;

  return (
    <div>
      <header className="relative z-30 border-b border-line-soft bg-surface">
        <div className="mx-auto flex max-w-[1800px] flex-wrap items-center justify-between gap-2 px-4 py-2">
          <div className="flex min-w-0 flex-wrap items-center gap-4">
            <div>
              <p className="eyebrow">Custom model</p>
              <h2 id={titleId} className="font-display text-heading-compact text-ink">
                Model <span className="text-accent">creator</span>
              </h2>
            </div>
            <details
              ref={detailsRef}
              className="group/model-details relative"
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  event.preventDefault();
                  event.stopPropagation();
                  detailsRef.current?.removeAttribute("open");
                }
              }}
            >
              <summary
                onClick={() => {
                  modelMenuRef.current?.removeAttribute("open");
                  guideRef.current?.removeAttribute("open");
                  setEditorOpen(false);
                }}
                className="flex max-w-60 cursor-pointer list-none items-center gap-2 rounded border border-line-soft bg-white px-3 py-2 text-sm text-ink transition-colors group-open/model-details:border-accent hover:border-accent hover:bg-accent/5 [&::-webkit-details-marker]:hidden"
                aria-label="Model details"
                title="Model details"
              >
                <span className="truncate text-ink">Model details</span>
                <ChevronDown
                  aria-hidden="true"
                  className="size-3.5 shrink-0 text-ink-3 transition-transform group-open/model-details:rotate-180"
                />
              </summary>
              <div className="fixed inset-x-4 top-20 z-30 mt-2 grid gap-3 rounded-md border border-line-soft bg-white p-4 shadow-lg lg:absolute lg:inset-x-auto lg:top-full lg:left-0 lg:w-80">
                <p className="eyebrow">Model details</p>
                <TextField
                  label="Model name"
                  value={draft.name}
                  onChange={(event) => {
                    dispatch({
                      type: "setModelInfo",
                      patch: { name: event.target.value },
                    });
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
                <Button
                  variant="ghost"
                  onClick={() => {
                    detailsRef.current?.removeAttribute("open");
                  }}
                >
                  Done
                </Button>
              </div>
            </details>
            <details
              ref={modelMenuRef}
              className="relative"
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  event.preventDefault();
                  event.stopPropagation();
                  modelMenuRef.current?.removeAttribute("open");
                }
              }}
            >
              <summary
                aria-label="Model actions menu"
                aria-description={modelStatus}
                title={modelStatus}
                onClick={() => {
                  detailsRef.current?.removeAttribute("open");
                  guideRef.current?.removeAttribute("open");
                  setEditorOpen(false);
                }}
                className="flex cursor-pointer list-none items-center gap-2 rounded border border-line-soft bg-white px-3 py-2 text-sm text-ink transition-colors hover:border-accent [&::-webkit-details-marker]:hidden"
              >
                {issueCount ? (
                  <CircleAlert aria-hidden="true" className="size-3.5 text-red-deep" />
                ) : (
                  <CircleCheck aria-hidden="true" className="size-3.5 text-[#5b9b72]" />
                )}
                Model actions
                {issueCount > 0 && (
                  <span
                    aria-hidden="true"
                    className="flex min-w-4 items-center justify-center rounded bg-red/10 px-1 font-mono text-[10px] text-red-deep"
                  >
                    {issueCount}
                  </span>
                )}
                <ChevronDown aria-hidden="true" className="size-3.5 text-ink-3" />
              </summary>
              <div
                className="fixed inset-x-4 top-32 z-30 mt-2 flex max-h-[calc(100dvh-9rem)] flex-col gap-1 overflow-auto rounded-md border border-line-soft bg-white p-2 shadow-lg lg:absolute lg:inset-x-auto lg:top-full lg:left-0 lg:w-64"
                aria-label="Model actions"
              >
                <div
                  className="mb-1 border-b border-line-soft px-2 py-3 text-xs"
                  role="status"
                >
                  <p
                    className={cn(
                      "flex items-center gap-2 font-medium",
                      issueCount ? "text-red-deep" : "text-ink-2",
                    )}
                  >
                    {issueCount ? (
                      <CircleAlert aria-hidden="true" className="size-4 shrink-0" />
                    ) : (
                      <CircleCheck
                        aria-hidden="true"
                        className="size-4 shrink-0 text-[#5b9b72]"
                      />
                    )}
                    {modelStatus}
                  </p>
                  {issueCount > 0 && (
                    <ul className="mt-2 max-h-40 list-disc space-y-1 overflow-auto pl-4 text-ink-3">
                      {[
                        ...modelIssues,
                        ...draft.beads.flatMap((bead) =>
                          (issues.beads[bead.key] ?? []).map(
                            (issue) => `${bead.beadId}: ${issue}`,
                          ),
                        ),
                      ].map((issue, index) => (
                        <li key={`${index.toString()}-${issue}`}>{issue}</li>
                      ))}
                    </ul>
                  )}
                  {issues.invalidConnections && (
                    <Button
                      variant="ghost"
                      className="mt-2"
                      onClick={() => {
                        dispatch({ type: "removeInvalidConnections" });
                      }}
                    >
                      Remove invalid connections
                    </Button>
                  )}
                </div>
                <Button
                  variant="ghost"
                  className="justify-start"
                  onClick={() => {
                    dispatch({ type: "replace", draft: createEmptyDraft() });
                    setEditorOpen(false);
                    modelMenuRef.current?.removeAttribute("open");
                  }}
                >
                  Start from scratch
                </Button>
                <Button
                  variant="ghost"
                  className="justify-start"
                  onClick={() => {
                    dispatch({ type: "replace", draft: createDefaultDraft() });
                    setEditorOpen(false);
                    modelMenuRef.current?.removeAttribute("open");
                  }}
                >
                  Load SimRNA template
                </Button>
                <Button
                  variant="ghost"
                  className="justify-start"
                  onClick={() => {
                    importInputRef.current?.click();
                    modelMenuRef.current?.removeAttribute("open");
                  }}
                >
                  Import model from JSON
                </Button>
                <Button
                  variant="ghost"
                  className="justify-start"
                  disabled={tooLarge}
                  onClick={handleExport}
                >
                  Export model as JSON
                </Button>
              </div>
            </details>
            <div className="relative flex items-center gap-2">
              <details
                ref={guideRef}
                className="relative"
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    event.preventDefault();
                    event.stopPropagation();
                    guideRef.current?.removeAttribute("open");
                    guideRef.current?.querySelector("summary")?.focus();
                  }
                }}
              >
                <summary
                  className="cursor-pointer list-none rounded border border-line-soft bg-white px-3 py-2 text-sm text-ink transition-colors hover:border-accent hover:text-accent [&::-webkit-details-marker]:hidden"
                  onClick={() => {
                    modelMenuRef.current?.removeAttribute("open");
                    detailsRef.current?.removeAttribute("open");
                    setEditorOpen(false);
                  }}
                >
                  User guide
                </summary>
                <section
                  aria-label="Creator instructions"
                  className="fixed inset-x-4 top-32 z-40 mt-2 max-h-[calc(100dvh-9rem)] overflow-auto rounded-md border border-line-soft bg-white p-5 shadow-lg lg:absolute lg:inset-x-auto lg:top-full lg:left-0 lg:max-h-[min(70dvh,640px)] lg:w-[min(42rem,50vw)]"
                >
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <h3 className="eyebrow">User guide</h3>
                    <Button
                      variant="ghost"
                      aria-label="Close user guide"
                      onClick={() => {
                        guideRef.current?.removeAttribute("open");
                        guideRef.current?.querySelector("summary")?.focus();
                      }}
                    >
                      Close
                    </Button>
                  </div>
                  <CreatorGuide />
                </section>
              </details>
            </div>
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
      <div className="mx-auto grid max-w-[1800px] gap-3 px-4 py-3 [--creator-height:calc(100dvh-80px)] lg:grid-cols-[minmax(0,1.75fr)_minmax(0,1fr)]">
        <div className="min-w-0 lg:h-[var(--creator-height)] lg:min-h-[480px]">
          <MoleculeEditor
            draft={draft}
            active={active}
            onSelect={(key) => {
              setSelectedKey(key);
            }}
            onRemove={(key) => {
              dispatch({ type: "removeBead", key });
            }}
            beadSettings={beadSettings}
            onEdit={() => {
              if (editorOpen) closeEditor();
              else openEditor();
            }}
            onAtom={(atom) => {
              if (active) dispatch({ type: "toggleAtom", key: active.key, atom });
            }}
            onScopeAtom={(scope, atom) => {
              if (active) {
                dispatch({
                  type: "setBeadScope",
                  key: active.key,
                  scope,
                  keepAtoms: true,
                  atom,
                });
              }
            }}
            onConnect={(first, second) => {
              dispatch({ type: "toggleIntraConnection", first, second });
            }}
            onInterConnect={(source, target) => {
              dispatch({ type: "setInterConnection", end: "source", beadId: source });
              dispatch({ type: "setInterConnection", end: "target", beadId: target });
            }}
            onClearInter={() => {
              dispatch({ type: "clearInterConnection" });
            }}
            onAdd={(strategy) => {
              const next = draftReducer(draft, { type: "addBead", strategy });
              dispatch({ type: "replace", draft: next });
              openEditor(next.beads.at(-1)?.key);
            }}
          />
        </div>
        <aside
          aria-label="Model preview"
          className="flex min-w-0 flex-col overflow-hidden rounded-md border border-line-soft bg-white lg:h-[var(--creator-height)] lg:min-h-[480px]"
        >
          <div
            role="group"
            aria-label="Preview mode"
            className="flex items-center gap-2 border-b border-line-soft px-3 py-2"
          >
            <Button
              variant="ghost"
              aria-pressed={previewTab === "live"}
              className={previewTab === "live" ? "border-accent text-accent" : ""}
              onClick={() => {
                setPreviewTab("live");
              }}
            >
              Live preview
            </Button>
            <span className="text-xs text-ink-3">or</span>
            <Button
              variant="ghost"
              aria-pressed={previewTab === "json"}
              className={previewTab === "json" ? "border-accent text-accent" : ""}
              onClick={() => {
                setPreviewTab("json");
              }}
            >
              JSON preview
            </Button>
          </div>
          <div className={cn("min-h-0 flex-1", previewTab !== "live" && "hidden")}>
            <Suspense
              fallback={
                <p role="status" className="p-4 text-sm text-ink-3">
                  Loading live preview…
                </p>
              }
            >
              <CreatorPreview
                draft={draft}
                presetIds={config.preset_ids}
                valid={
                  draft.beads.length > 0 &&
                  Object.keys(issues.beads).length === 0 &&
                  issues.model.every((issue) => issue === "Enter a model name.")
                }
              />
            </Suspense>
          </div>
          {previewTab === "json" && (
            <div className="flex min-h-0 flex-1 flex-col gap-2 p-3">
              <p
                className={cn(
                  "font-mono text-xs",
                  tooLarge ? "text-red-deep" : "text-ink-3",
                )}
              >
                {json.length.toLocaleString("en-US")} /{" "}
                {config.custom_model_json_max_chars.toLocaleString("en-US")} characters
              </p>
              <pre className="min-h-0 flex-1 overflow-auto rounded border border-line-soft bg-surface p-3 font-mono text-xs text-ink-2">
                {json}
              </pre>
            </div>
          )}
        </aside>
      </div>
      {importError && (
        <div className="fixed right-4 bottom-4 z-50 max-w-md">
          <Alert severity="error">{importError}</Alert>
        </div>
      )}
    </div>
  );
}
