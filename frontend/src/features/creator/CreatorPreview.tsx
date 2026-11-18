import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { SelectField } from "@/components/ui/SelectField";
import { ToggleButton } from "@/components/ui/ToggleButton";
import {
  createMolstarViewer,
  type MolstarViewer,
  type StructureId,
  type StructureInput,
} from "@/features/results/viewer/molstarViewer";
import { STRUCTURE_COLORS } from "@/features/results/viewer/structureColors";
import { formatPercent } from "@/lib/format";

import { ALL_RESIDUES, type Residue } from "./atoms";
import type { ModelDraft } from "./modelDraft";
import { buildPreview, readPreviewSource } from "./previewStructure";

interface PreviewSession {
  target: HTMLDivElement;
  viewer: MolstarViewer | null;
  queue: Promise<void>;
  active: boolean;
  shownData: Partial<Record<StructureId, string>>;
}

export default function CreatorPreview({
  draft,
  presetIds,
  valid,
}: {
  draft: ModelDraft;
  presetIds: string[];
  valid: boolean;
}) {
  const [preset, setPreset] = useState(presetIds[0] ?? "1EHZ");
  const [selection, setSelection] = useState<"all" | Residue>("all");
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [status, setStatus] = useState("Loading example…");
  const [display, setDisplay] = useState({ coarse: true, reference: false });
  const container = useRef<HTMLDivElement>(null);
  const sessionRef = useRef<PreviewSession | null>(null);
  const displayRef = useRef(display);

  useEffect(() => {
    displayRef.current = display;
    sessionRef.current?.viewer?.setVisibility("reference", display.reference);
    sessionRef.current?.viewer?.setVisibility("coarse", display.coarse);
  }, [display]);

  const example = useQuery({
    queryKey: ["creator-example", preset, revision],
    queryFn: async ({ signal }) => {
      const response = await fetch(
        `/static/presets/${encodeURIComponent(preset)}.cif`,
        { signal },
      );
      if (!response.ok) throw new Error("Could not download the example.");
      return readPreviewSource(await response.text());
    },
    staleTime: Infinity,
    retry: false,
  });
  const preview = useMemo(
    () =>
      example.data
        ? buildPreview(
            draft,
            example.data.residues,
            selection,
            example.data.originalAtomCount,
          )
        : null,
    [draft, example.data, selection],
  );

  useEffect(() => {
    const target = document.createElement("div");
    target.className = "absolute inset-0";
    container.current?.append(target);
    const session: PreviewSession = {
      target,
      viewer: null,
      queue: Promise.resolve(),
      active: true,
      shownData: {},
    };
    sessionRef.current = session;
    return () => {
      session.active = false;
      void session.queue.then(() => session.viewer?.dispose());
      sessionRef.current = null;
      target.remove();
    };
  }, [revision, preset, selection]);

  useEffect(() => {
    if (!preview || !valid) return;
    const session = sessionRef.current;
    if (!session) return;
    session.target.hidden = !preview.count;
    let cancelled = false;
    const isCurrent = () => !cancelled && session.active;
    const timer = window.setTimeout(() => {
      session.queue = session.queue
        .then(async () => {
          if (!isCurrent()) return;
          if (!preview.count) {
            setStatus("No mapped atoms in this selection. Choose another preview.");
            return;
          }
          setStatus("Updating preview…");
          const instance = session.viewer;
          if (!instance) {
            const created = await createMolstarViewer(session.target, inputs(preview));
            if (!session.active) {
              created.dispose();
              return;
            }
            if (created.failedStructures.length) {
              created.dispose();
              throw new Error("Could not load preview structures.");
            }
            session.viewer = created;
            for (const input of inputs(preview))
              session.shownData[input.id] = input.data;
            created.setVisibility("reference", displayRef.current.reference);
            created.setVisibility("coarse", displayRef.current.coarse);
          } else {
            for (const input of inputs(preview)) {
              if (!isCurrent()) return;
              if (session.shownData[input.id] !== input.data) {
                await instance.replaceStructure(input);
                if (!session.active) return;
                session.shownData[input.id] = input.data;
              }
            }
          }
          if (isCurrent()) {
            setStatus("");
            setError(null);
          }
        })
        .catch(() => {
          if (isCurrent()) {
            setError("Could not update the Molstar preview. Try reloading it.");
            setStatus("");
          }
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [preview, valid, revision, preset, selection]);

  return (
    <section
      aria-label="Live structure preview"
      className="flex h-full min-h-0 flex-col gap-2 p-3"
    >
      <div className="grid grid-cols-2 gap-2">
        <SelectField
          label="Example structure"
          value={preset}
          onChange={(event) => {
            setPreset(event.target.value);
            setError(null);
          }}
        >
          {presetIds.map((id) => (
            <option key={id}>{id}</option>
          ))}
        </SelectField>
        <SelectField
          label="Preview residues"
          value={selection}
          onChange={(event) => {
            const value = event.target.value;
            if (value === "all" || ALL_RESIDUES.includes(value as Residue))
              setSelection(value as "all" | Residue);
          }}
        >
          <option value="all">All RNA residues</option>
          {ALL_RESIDUES.map((base) => (
            <option key={base} value={base}>
              One {base} nucleotide
            </option>
          ))}
        </SelectField>
      </div>
      <div role="group" aria-label="Preview display" className="flex flex-wrap gap-2">
        {(["coarse", "reference"] as const).map((id) => (
          <ToggleButton
            key={id}
            pressed={display[id]}
            onClick={() => {
              setDisplay((previous) => ({ ...previous, [id]: !previous[id] }));
            }}
          >
            {id === "coarse" ? "Coarse-grained" : "All-atom"}
          </ToggleButton>
        ))}
      </div>
      <div
        ref={container}
        className="relative min-h-64 flex-1 overflow-hidden rounded-md border border-line-soft bg-white lg:min-h-0"
        aria-label="Molstar live preview"
      >
        {(status || !valid || example.isPending) && !example.error && (
          <div
            role="status"
            className="absolute inset-x-2 top-2 z-10 rounded border border-line-soft bg-white/95 px-3 py-2 text-xs text-ink-3"
          >
            {!valid
              ? "Resolve model issues to update the preview. The last valid model stays visible."
              : example.isPending
                ? "Loading example…"
                : status}
          </div>
        )}
      </div>
      {(error ?? example.error) && (
        <Alert severity="error">
          <p>{error ?? example.error?.message}</p>
          <Button
            variant="ghost"
            className="mt-2"
            onClick={() => {
              setError(null);
              setRevision((value) => value + 1);
            }}
          >
            Reload preview
          </Button>
        </Alert>
      )}
      <dl
        aria-label="Preview atom counts"
        className="grid grid-cols-3 gap-2 border-t border-line-soft pt-2 text-xs"
        title="Input atoms are counted as in Results: first-model polymer atoms, including modified residues and protein. Water and ligands are excluded. Counts follow the selected preview."
      >
        <div>
          <dt className="text-[10px] text-ink-3">Input atoms (AA)</dt>
          <dd className="mt-0.5 font-mono text-sm text-ink">
            {preview ? preview.atomCounts.original.toLocaleString("en-US") : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] text-ink-3">CG beads</dt>
          <dd className="mt-0.5 font-mono text-sm text-ink">
            {preview && valid ? preview.atomCounts.coarse.toLocaleString("en-US") : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] text-ink-3">Atom reduction</dt>
          <dd className="mt-0.5 font-mono text-sm text-accent">
            {preview && valid ? formatPercent(preview.atomCounts.reduction) : "—"}
          </dd>
        </div>
      </dl>
    </section>
  );
}

function inputs(preview: ReturnType<typeof buildPreview>): StructureInput[] {
  return [
    {
      id: "reference",
      data: preview.reference,
      format: "mmcif",
      color: STRUCTURE_COLORS.reference,
      isCoarse: false,
    },
    {
      id: "coarse",
      data: preview.coarse,
      format: "mmcif",
      color: STRUCTURE_COLORS.coarse,
      isCoarse: true,
    },
  ];
}
