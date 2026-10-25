import { type ReactNode, useEffect, useRef, useState } from "react";

import type { ResultStructures } from "@/api/results";
import { Alert } from "@/components/ui/Alert";
import { SelectField } from "@/components/ui/SelectField";
import { ToggleButton } from "@/components/ui/ToggleButton";

import {
  type ColorMode,
  createMolstarViewer,
  type MolstarViewer,
  type RepresentationType,
  type StructureId,
} from "./molstarViewer";
import { STRUCTURE_COLORS } from "./structureColors";

interface StructureViewerProps {
  structures: ResultStructures;
  referenceFormat: "mmcif" | "pdb";
}

const STRUCTURE_TOGGLES: readonly { id: StructureId; label: string; name: string }[] = [
  { id: "coarse", label: "CG model", name: "CG model" },
  { id: "reference", label: "Input structure (all-atom)", name: "input structure" },
];

const REPRESENTATIONS: readonly { type: RepresentationType; label: string }[] = [
  { type: "ball-and-stick", label: "Ball & stick" },
  { type: "cartoon", label: "Cartoon" },
  { type: "backbone", label: "Backbone" },
];

const COLOR_MODES: readonly { mode: ColorMode; label: string }[] = [
  { mode: "uniform", label: "Single color" },
  { mode: "element-symbol", label: "Element" },
  { mode: "chain-id", label: "Chain" },
  { mode: "residue-name", label: "Residue" },
];

type ViewerStatus = "loading" | "ready" | "unreadable" | "error";

const STATUS_MESSAGES: Record<Exclude<ViewerStatus, "ready">, string> = {
  loading: "Loading structures…",
  unreadable: "Neither structure could be displayed.",
  error: "The structure viewer could not be started.",
};

export function StructureViewer({ structures, referenceFormat }: StructureViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<MolstarViewer | null>(null);
  const [status, setStatus] = useState<ViewerStatus>("loading");
  const [busy, setBusy] = useState(false);
  const [visible, setVisible] = useState<Record<StructureId, boolean>>({
    reference: true,
    coarse: true,
  });
  const [representation, setRepresentation] =
    useState<RepresentationType>("ball-and-stick");
  const [colorMode, setColorMode] = useState<ColorMode>("uniform");
  const [failedStructures, setFailedStructures] = useState<readonly StructureId[]>([]);
  const [hasNonPolymer, setHasNonPolymer] = useState(false);
  const [nonPolymerVisible, setNonPolymerVisible] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const target = document.createElement("div");
    target.className = "absolute inset-0";
    container.append(target);

    let disposed = false;
    createMolstarViewer(target, [
      {
        id: "reference",
        data: structures.reference,
        format: referenceFormat,
        color: STRUCTURE_COLORS.reference,
        isCoarse: false,
      },
      {
        id: "coarse",
        data: structures.coarseMmcif,
        format: "mmcif",
        color: STRUCTURE_COLORS.coarse,
        isCoarse: true,
      },
    ]).then(
      (viewer) => {
        if (disposed) {
          viewer.dispose();
          return;
        }
        viewerRef.current = viewer;
        for (const id of viewer.failedStructures) {
          console.error(`Could not load the ${id} structure into the viewer.`);
        }
        setFailedStructures(viewer.failedStructures);
        setHasNonPolymer(viewer.hasNonPolymer);
        setStatus("ready");
      },
      (error: unknown) => {
        console.error("Could not initialize the structure viewer.", error);
        if (!disposed) {
          setStatus(error instanceof AggregateError ? "unreadable" : "error");
        }
      },
    );

    return () => {
      disposed = true;
      viewerRef.current?.dispose();
      viewerRef.current = null;
      target.remove();
    };
  }, [structures, referenceFormat]);

  const runViewerAction = async (action: (viewer: MolstarViewer) => Promise<void>) => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    setBusy(true);
    try {
      await action(viewer);
    } catch (error) {
      console.error("Could not update the structure viewer.", error);
    } finally {
      setBusy(false);
    }
  };

  const toggleStructure = (id: StructureId) => {
    const nextVisible = !visible[id];
    viewerRef.current?.setVisibility(id, nextVisible);
    setVisible((current) => ({ ...current, [id]: nextVisible }));
  };

  const toggleNonPolymer = () => {
    viewerRef.current?.setNonPolymerVisibility(!nonPolymerVisible);
    setNonPolymerVisible(!nonPolymerVisible);
  };

  const changeRepresentation = (type: RepresentationType) =>
    runViewerAction(async (viewer) => {
      await viewer.setRepresentation("reference", type);
      setRepresentation(type);
    });

  const changeColorMode = (mode: ColorMode) =>
    runViewerAction(async (viewer) => {
      await viewer.setColorMode("reference", mode);
      setColorMode(mode);
    });

  const controlsDisabled = status !== "ready" || busy;
  const referenceControlsDisabled =
    controlsDisabled || failedStructures.includes("reference");
  const failedNames = STRUCTURE_TOGGLES.filter(({ id }) =>
    failedStructures.includes(id),
  ).map(({ name }) => name);

  return (
    <div className="flex flex-col gap-3">
      <div
        ref={containerRef}
        className="relative h-[55dvh] min-h-80 overflow-hidden rounded-md border border-line-soft bg-white"
      >
        {status !== "ready" && (
          <p
            role={status === "loading" ? "status" : "alert"}
            className="absolute inset-0 z-10 flex items-center justify-center bg-white font-mono text-label tracking-[0.15em] text-ink-3 uppercase"
          >
            {STATUS_MESSAGES[status]}
          </p>
        )}
      </div>

      {failedNames.length > 0 && (
        <Alert severity="error">
          The {failedNames.join(" and ")} could not be displayed. The downloads are not
          affected.
        </Alert>
      )}

      <div className="flex flex-col gap-3">
        <ControlGroup label="Display">
          {STRUCTURE_TOGGLES.map(({ id, label }) => (
            <ToggleButton
              key={id}
              pressed={visible[id] && !failedStructures.includes(id)}
              disabled={controlsDisabled || failedStructures.includes(id)}
              onClick={() => {
                toggleStructure(id);
              }}
            >
              <span
                aria-hidden="true"
                className="size-2 rounded-full"
                style={{ backgroundColor: toCssColor(STRUCTURE_COLORS[id]) }}
              />
              {label}
            </ToggleButton>
          ))}
          {hasNonPolymer && (
            <ToggleButton
              pressed={nonPolymerVisible}
              disabled={controlsDisabled}
              onClick={toggleNonPolymer}
            >
              Water, ions &amp; ligands
            </ToggleButton>
          )}
        </ControlGroup>

        <ControlGroup label="Input structure">
          <InlineSelect
            label="Color by"
            value={colorMode}
            disabled={referenceControlsDisabled}
            onChange={(mode) => void changeColorMode(mode)}
            options={COLOR_MODES.map(({ mode, label }) => ({ value: mode, label }))}
          />
          <InlineSelect
            label="Representation"
            value={representation}
            disabled={referenceControlsDisabled}
            onChange={(type) => void changeRepresentation(type)}
            options={REPRESENTATIONS.map(({ type, label }) => ({ value: type, label }))}
          />
        </ControlGroup>
      </div>
    </div>
  );
}

function ControlGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap items-center gap-2">
      <span aria-hidden="true" className="eyebrow">
        {label}
      </span>
      {children}
    </div>
  );
}

interface InlineSelectProps<T extends string> {
  label: string;
  value: T;
  disabled: boolean;
  options: readonly { value: T; label: string }[];
  onChange: (value: T) => void;
}

function InlineSelect<T extends string>({
  label,
  value,
  disabled,
  options,
  onChange,
}: InlineSelectProps<T>) {
  return (
    <SelectField
      label={label}
      value={value}
      disabled={disabled}
      inline
      onChange={(event) => {
        const option = options.find(({ value }) => value === event.target.value);

        if (option) onChange(option.value);
      }}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </SelectField>
  );
}

function toCssColor(color: number): string {
  return `#${color.toString(16).padStart(6, "0")}`;
}
