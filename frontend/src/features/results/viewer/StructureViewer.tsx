import { type ReactNode, useEffect, useRef, useState } from "react";

import type { ResultStructures } from "@/api/results";
import { ToggleButton } from "@/components/ui/ToggleButton";

import {
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

const STRUCTURE_TOGGLES: readonly { id: StructureId; label: string }[] = [
  { id: "coarse", label: "Coarse-grained" },
  { id: "reference", label: "All-atom" },
];

const REPRESENTATIONS: readonly { type: RepresentationType; label: string }[] = [
  { type: "ball-and-stick", label: "Ball & stick" },
  { type: "cartoon", label: "Cartoon" },
  { type: "backbone", label: "Backbone" },
];

type ViewerStatus = "loading" | "ready" | "error";

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
  const [colorByElement, setColorByElement] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Mol* mounts its own React root, so every mount gets a fresh target element.
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
        setStatus("ready");
      },
      (error: unknown) => {
        console.error("Could not initialize the structure viewer.", error);
        if (!disposed) setStatus("error");
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

  const changeRepresentation = (type: RepresentationType) =>
    runViewerAction(async (viewer) => {
      await viewer.setRepresentation(type);
      setRepresentation(type);
    });

  const toggleElementColors = () =>
    runViewerAction(async (viewer) => {
      await viewer.setColorMode(
        "reference",
        colorByElement ? "uniform" : "element-symbol",
      );
      setColorByElement(!colorByElement);
    });

  const controlsDisabled = status !== "ready" || busy;

  return (
    <div className="flex flex-col gap-3">
      <div
        ref={containerRef}
        className="relative h-[55dvh] min-h-80 overflow-hidden rounded-md border border-line-soft bg-white"
      >
        {status !== "ready" && (
          <p
            role={status === "error" ? "alert" : "status"}
            className="absolute inset-0 z-10 flex items-center justify-center bg-white font-mono text-label tracking-[0.15em] text-ink-3 uppercase"
          >
            {status === "error"
              ? "The structure viewer could not be started."
              : "Loading structures…"}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <ControlGroup label="Show">
          {STRUCTURE_TOGGLES.map(({ id, label }) => (
            <ToggleButton
              key={id}
              pressed={visible[id]}
              disabled={controlsDisabled}
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
        </ControlGroup>

        <ControlGroup label="Style">
          {REPRESENTATIONS.map(({ type, label }) => (
            <ToggleButton
              key={type}
              pressed={representation === type}
              disabled={controlsDisabled}
              onClick={() => void changeRepresentation(type)}
            >
              {label}
            </ToggleButton>
          ))}
        </ControlGroup>

        <ControlGroup label="All-atom color">
          <ToggleButton
            pressed={colorByElement}
            disabled={controlsDisabled}
            onClick={() => void toggleElementColors()}
          >
            By element
          </ToggleButton>
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

function toCssColor(color: number): string {
  return `#${color.toString(16).padStart(6, "0")}`;
}
