import { ChevronDown, X } from "lucide-react";
import { type ReactNode, useId, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { SelectField } from "@/components/ui/SelectField";
import { ToggleButton } from "@/components/ui/ToggleButton";

import {
  ALL_RESIDUES,
  BEAD_STRATEGIES,
  type BeadScope,
  type BeadStrategy,
  type Residue,
  residuesForScope,
  SCOPES,
  STRATEGY_LABELS,
} from "./atoms";
import { beadColor } from "./beadAppearance";
import {
  atomSelection,
  type BeadDraft,
  type ModelDraft,
  positionConflict,
} from "./modelDraft";
import {
  availableDiagramAtom,
  beadLabels,
  beadPoint,
  isDoubleBond,
  nucleotideDiagram,
} from "./nucleotideDiagram";

interface Props {
  draft: ModelDraft;
  active: BeadDraft | undefined;
  onSelect: (key: string) => void;
  onRemove: (key: string) => void;
  onEdit: () => void;
  beadSettings?: ReactNode;
  onAtom: (atom: string) => void;
  onConnect: (first: string, second: string) => void;
  onAdd: (strategy: BeadStrategy) => void;
  onScopeAtom: (scope: BeadScope, atom: string) => void;
  onInterConnect: (source: string, target: string) => void;
  onClearInter: () => void;
}

const NAMES = { A: "Adenine", G: "Guanine", C: "Cytosine", U: "Uracil" };
const NOTICE_CLASSES =
  "absolute bottom-3 left-1/2 z-20 w-fit max-w-[min(24rem,calc(100%_-_1.5rem))] -translate-x-1/2 rounded border border-red bg-white px-2.5 py-2 text-xs shadow-lg";
export function MoleculeEditor({
  draft,
  active,
  onSelect,
  onRemove,
  onEdit,
  beadSettings,
  onAtom,
  onConnect,
  onAdd,
  onScopeAtom,
  onInterConnect,
  onClearInter,
}: Props) {
  const id = useId();
  const selectorRef = useRef<HTMLDetailsElement>(null);
  const [tool, setTool] = useState<"atoms" | "intra" | "inter">("atoms");
  const [connectionType, setConnectionType] = useState<"intra" | "inter">("intra");
  const [adding, setAdding] = useState(false);
  const [conflictHint, setConflictHint] = useState<{
    key: string;
    message: string;
  } | null>(null);
  const [scopeHint, setScopeHint] = useState<{
    key: string;
    atom: string;
    scope: BeadScope;
  } | null>(null);
  const [connectionStart, setConnectionStart] = useState<string | null>(null);
  const connectMode = tool !== "atoms";
  const selectBead = (bead: BeadDraft) => {
    if (!connectMode) {
      setConflictHint(null);
      setScopeHint(null);
      onSelect(bead.key);
      return;
    }
    if (
      connectionStart &&
      (tool === "inter" || connectionStart !== bead.beadId) &&
      draft.beads.some((candidate) => candidate.beadId === connectionStart)
    ) {
      if (tool === "inter") onInterConnect(connectionStart, bead.beadId);
      else onConnect(connectionStart, bead.beadId);
      setConnectionStart(null);
    } else setConnectionStart(bead.beadId);
  };
  const chooseAtom = (residue: Residue, atom: string, enabled: boolean) => {
    if (!active || connectMode) return;
    const conflict = positionConflict(draft, atomSelection(active, atom));
    if (conflict) {
      setScopeHint(null);
      setConflictHint({ key: active.key, message: conflict });
      return;
    }
    setConflictHint(null);
    if (enabled) {
      setScopeHint(null);
      onAtom(atom);
      return;
    }
    const scopes: BeadScope[] = [
      "purine",
      "pyrimidine",
      "adenine",
      "cytosine",
      "guanine",
      "uracil",
    ];
    const scope = scopes.find(
      (scope) =>
        residuesForScope(scope).includes(residue) && SCOPES[scope].atoms.includes(atom),
    );
    if (scope) setScopeHint({ key: active.key, atom, scope });
  };
  const instruction =
    tool === "atoms"
      ? "Click highlighted atoms. Other atoms offer a change of mapping scope."
      : connectionStart
        ? `Source ${connectionStart} selected. Choose ${tool === "inter" ? "a target in residue i+1" : "another bead"}.`
        : tool === "inter"
          ? "Click a source bead in residue i, then a target bead in residue i+1."
          : "Click two bead labels to add or remove an intra-residue connection.";
  return (
    <section
      aria-label="2D model editor"
      className="relative flex h-full min-h-0 flex-col rounded-md border border-line-soft bg-white"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line-soft px-3 py-2">
        <h3 className="eyebrow">2D model editor</h3>
        <div className="ml-auto flex min-w-0 flex-wrap items-center gap-2">
          <details
            ref={selectorRef}
            className="relative"
            onBlur={(event) => {
              if (
                !(event.relatedTarget instanceof Node) ||
                !event.currentTarget.contains(event.relatedTarget)
              )
                selectorRef.current?.removeAttribute("open");
            }}
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                selectorRef.current?.removeAttribute("open");
                selectorRef.current?.querySelector("summary")?.focus();
                return;
              }
              if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
              const options = Array.from(
                event.currentTarget.querySelectorAll<HTMLButtonElement>(
                  '[role="menuitemradio"]',
                ),
              );
              if (!options.length) return;
              event.preventDefault();
              event.currentTarget.open = true;
              const current = options.findIndex(
                (option) => option === document.activeElement,
              );
              const index =
                event.key === "Home"
                  ? 0
                  : event.key === "End"
                    ? options.length - 1
                    : current < 0
                      ? Math.max(
                          0,
                          draft.beads.findIndex((bead) => bead.key === active?.key),
                        )
                      : (current +
                          (event.key === "ArrowDown" ? 1 : -1) +
                          options.length) %
                        options.length;
              options[index]?.focus();
            }}
          >
            <summary
              aria-label="Select bead"
              aria-haspopup="menu"
              className="flex cursor-pointer list-none items-center gap-2 rounded border border-line-soft bg-white px-2.5 py-1.5 text-xs text-ink transition-colors hover:border-accent [&::-webkit-details-marker]:hidden"
            >
              <span className="text-ink-3">Select bead</span>
              {active ? (
                <>
                  <span
                    aria-hidden="true"
                    className="size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: beadColor(draft, active) }}
                  />
                  <strong style={{ color: beadColor(draft, active) }}>
                    {active.beadId} · {active.name}
                  </strong>
                </>
              ) : (
                <span>No beads yet</span>
              )}
              <ChevronDown aria-hidden="true" className="size-3.5 text-ink-3" />
            </summary>
            <div
              role="menu"
              aria-label="Available beads"
              className="absolute top-full left-0 z-50 mt-2 max-h-64 w-64 max-w-[calc(100vw-3.5rem)] overflow-auto rounded-md border border-line-soft bg-white p-1 shadow-lg lg:right-0 lg:left-auto"
            >
              {draft.beads.map((bead) => (
                <div key={bead.key} role="none" className="flex items-center gap-1">
                  <button
                    type="button"
                    role="menuitemradio"
                    aria-checked={active?.key === bead.key}
                    className="flex min-w-0 flex-1 cursor-pointer items-center gap-2 rounded px-3 py-2 text-left text-xs hover:bg-accent/5 focus-visible:bg-accent/5"
                    onClick={() => {
                      setScopeHint(null);
                      onSelect(bead.key);
                      selectorRef.current?.removeAttribute("open");
                      selectorRef.current?.querySelector("summary")?.focus();
                    }}
                  >
                    <span
                      aria-hidden="true"
                      className="size-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: beadColor(draft, bead) }}
                    />
                    <span>
                      <strong
                        className="block"
                        style={{ color: beadColor(draft, bead) }}
                      >
                        {bead.beadId} · {bead.name}
                      </strong>
                      <span className="text-[10px] text-ink-3">
                        {SCOPES[bead.scope].label}
                      </span>
                    </span>
                  </button>
                  <button
                    type="button"
                    role="menuitem"
                    aria-label={`Remove bead ${bead.beadId} (${bead.name}, ${SCOPES[bead.scope].label}) from list`}
                    title="Remove bead"
                    className="shrink-0 cursor-pointer rounded p-2 text-ink-3 hover:bg-red/5 hover:text-red-deep"
                    onClick={() => {
                      onRemove(bead.key);
                      setConnectionStart(null);
                      setScopeHint(null);
                      selectorRef.current?.querySelector("summary")?.focus();
                    }}
                  >
                    <X aria-hidden="true" className="size-4" />
                  </button>
                </div>
              ))}
              {!draft.beads.length && (
                <p className="p-3 text-xs text-ink-3">Add a bead to start.</p>
              )}
            </div>
          </details>
          <span className="sr-only" role="status" aria-label="Active bead summary">
            {active ? `${active.beadId} · ${active.name}` : "No bead selected"}
          </span>
          <div className="relative">
            <ToggleButton
              pressed={!!beadSettings}
              onClick={onEdit}
              disabled={!active}
              aria-label="Bead settings"
              aria-expanded={!!beadSettings}
              aria-controls={`${id}-bead-settings`}
            >
              Bead settings
            </ToggleButton>
            {beadSettings && <div id={`${id}-bead-settings`}>{beadSettings}</div>}
          </div>
        </div>
      </div>
      <div
        className="flex flex-wrap items-center gap-1.5 border-b border-line-soft bg-surface/70 px-3 py-2"
        role="group"
        aria-label="Editor tool"
        title={instruction}
      >
        <ToggleButton
          pressed={tool === "atoms"}
          onClick={() => {
            setTool("atoms");
            setConnectionStart(null);
            setScopeHint(null);
          }}
        >
          Map atoms
        </ToggleButton>
        <ToggleButton
          pressed={connectMode}
          onClick={() => {
            setTool(connectionType);
            setConnectionStart(null);
            setScopeHint(null);
          }}
        >
          Connect beads
        </ToggleButton>
        {connectMode && (
          <SelectField
            inline
            label={<span className="sr-only">Connection type</span>}
            value={connectionType}
            onChange={(event) => {
              const value = event.target.value;
              if (value === "intra" || value === "inter") {
                setTool(value);
                setConnectionType(value);
                setConnectionStart(null);
                setScopeHint(null);
              }
            }}
          >
            <option value="intra">Intra-residue</option>
            <option value="inter">Inter-residue</option>
          </SelectField>
        )}
        <div
          className="relative ml-auto"
          onBlur={(event) => {
            if (
              !(event.relatedTarget instanceof Node) ||
              !event.currentTarget.contains(event.relatedTarget)
            )
              setAdding(false);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape" && adding) {
              event.preventDefault();
              event.stopPropagation();
              setAdding(false);
            }
          }}
        >
          <Button
            variant="ghost"
            aria-haspopup="menu"
            aria-expanded={adding}
            onClick={() => {
              setAdding((value) => !value);
            }}
          >
            <span aria-hidden="true">+</span> Add bead
          </Button>
          {adding && (
            <div
              role="menu"
              aria-label="New bead strategy"
              className="absolute top-full right-0 z-30 mt-1 w-56 rounded border border-line-soft bg-white p-1 shadow-lg"
            >
              <p className="px-3 py-2 text-xs text-ink-3">Choose a mapping strategy</p>
              {BEAD_STRATEGIES.map((strategy) => (
                <button
                  key={strategy}
                  role="menuitem"
                  type="button"
                  className="w-full rounded px-3 py-2 text-left text-sm text-ink hover:bg-accent/10"
                  onClick={() => {
                    onAdd(strategy);
                    setAdding(false);
                    setTool("atoms");
                    setScopeHint(null);
                  }}
                >
                  {STRATEGY_LABELS[strategy]}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      {connectionStart && (
        <div role="status" className={NOTICE_CLASSES}>
          <p>{instruction}</p>
          <Button
            variant="ghost"
            className="mt-2"
            onClick={() => {
              setConnectionStart(null);
            }}
          >
            Dismiss
          </Button>
        </div>
      )}
      <div className="grid min-h-0 flex-1 grid-cols-1 min-[640px]:grid-cols-2 lg:grid-rows-2">
        {ALL_RESIDUES.map((residue) => {
          const { atoms, bonds } = nucleotideDiagram(residue);
          const applicable = draft.beads.filter((bead) =>
            residuesForScope(bead.scope).includes(residue),
          );
          const markers = beadLabels(applicable, atoms);
          const points = new Map(
            applicable.map((bead) => [bead.beadId, beadPoint(bead, atoms)]),
          );
          const editable = active && residuesForScope(active.scope).includes(residue);
          const isSelected = (bead: BeadDraft) =>
            connectMode ? connectionStart === bead.beadId : active?.key === bead.key;
          return (
            <div
              key={residue}
              className={`relative flex min-h-0 min-w-0 flex-col border-b border-line-soft/70 p-2 odd:min-[640px]:border-r ${editable ? "bg-white" : "bg-surface/70"}`}
              data-editable={!!editable}
            >
              <div className="flex items-center justify-between gap-2">
                <h4 className="flex items-center gap-2.5 text-sm font-medium text-ink">
                  <span className="flex size-5 items-center justify-center rounded border border-accent/20 bg-accent/5 font-mono text-xs text-accent">
                    {residue}
                  </span>
                  {NAMES[residue]}
                </h4>
                <span
                  className={`font-mono text-[9px] tracking-wider ${editable ? "text-accent" : "text-ink-3"}`}
                >
                  <span aria-hidden="true">{editable ? "●" : "○"}</span>{" "}
                  {applicable.length} beads
                </span>
              </div>
              <svg
                viewBox="0 24 390 248"
                aria-label={`${NAMES[residue]} atom diagram`}
                className={`h-44 min-h-0 w-full lg:h-full lg:flex-1 ${editable ? "" : "opacity-45"}`}
              >
                <defs>
                  {markers.map(({ bead }) => (
                    <radialGradient
                      key={bead.key}
                      id={`${id}-${residue}-${bead.key}`}
                      cx="32%"
                      cy="28%"
                      r="75%"
                    >
                      <stop offset="0" stopColor="white" stopOpacity=".7" />
                      <stop
                        offset=".55"
                        stopColor={beadColor(draft, bead)}
                        stopOpacity=".9"
                      />
                      <stop offset="1" stopColor={beadColor(draft, bead)} />
                    </radialGradient>
                  ))}
                </defs>
                {bonds.map(([a, b]) => {
                  const from = atoms[a],
                    to = atoms[b];
                  if (!from || !to) return null;
                  const length = Math.hypot(to[0] - from[0], to[1] - from[1]);
                  const dx = (-(to[1] - from[1]) / length) * 2.1,
                    dy = ((to[0] - from[0]) / length) * 2.1;
                  return (
                    <g
                      key={`${a}-${b}`}
                      stroke="#7c8c97"
                      strokeWidth="1.7"
                      strokeLinecap="round"
                    >
                      {(isDoubleBond(residue, a, b) ? [-1, 1] : [0]).map((side) => (
                        <line
                          key={side}
                          x1={from[0] + side * dx}
                          y1={from[1] + side * dy}
                          x2={to[0] + side * dx}
                          y2={to[1] + side * dy}
                        />
                      ))}
                    </g>
                  );
                })}
                {draft.intraResidue.map(([a, b]) => {
                  const from = points.get(a),
                    to = points.get(b);
                  return from && to ? (
                    <line
                      key={`${a}-${b}`}
                      x1={from[0]}
                      y1={from[1]}
                      x2={to[0]}
                      y2={to[1]}
                      stroke="#0091c9"
                      strokeWidth="6"
                      strokeOpacity=".24"
                      strokeLinecap="round"
                    />
                  ) : null;
                })}
                {markers.map(({ bead, point: [x, y] }) => (
                  <g key={bead.key} pointerEvents="none">
                    {isSelected(bead) && (
                      <circle
                        cx={x}
                        cy={y}
                        r="22"
                        fill={beadColor(draft, bead)}
                        fillOpacity=".1"
                        stroke={beadColor(draft, bead)}
                        strokeWidth="1"
                        strokeDasharray={connectMode ? "3 3" : undefined}
                      />
                    )}
                    <circle
                      cx={x}
                      cy={y}
                      r="16"
                      fill={`url(#${id}-${residue}-${bead.key})`}
                      stroke={beadColor(draft, bead)}
                      strokeWidth="1.2"
                    />
                  </g>
                ))}
                {Object.entries(atoms).map(([atom, [x, y]]) => {
                  const conflict = active
                    ? positionConflict(draft, atomSelection(active, atom))
                    : undefined;
                  const enabled =
                    !conflict &&
                    !connectMode &&
                    !!editable &&
                    availableDiagramAtom(active, atom);
                  const selected = !!editable && active.atoms.includes(atom);
                  const mapped = markers.some(
                    ({ point }) => Math.hypot(point[0] - x, point[1] - y) < 9,
                  );
                  const color = atom.startsWith("O")
                    ? "#bb4848"
                    : atom.startsWith("N")
                      ? "#3276aa"
                      : atom === "P"
                        ? "#a36e1a"
                        : "#344b5a";
                  const selectedColor = active ? beadColor(draft, active) : "#0091c9";
                  return (
                    <g
                      key={atom}
                      role="button"
                      tabIndex={active && !connectMode ? 0 : -1}
                      aria-label={`${residue} atom ${atom}`}
                      aria-pressed={selected}
                      aria-disabled={!enabled}
                      onClick={() => {
                        chooseAtom(residue, atom, enabled);
                      }}
                      onKeyDown={(event) => {
                        if (
                          active &&
                          !connectMode &&
                          (event.key === "Enter" || event.key === " ")
                        ) {
                          event.preventDefault();
                          chooseAtom(residue, atom, enabled);
                        }
                      }}
                      className={
                        conflict
                          ? "cursor-help"
                          : enabled
                            ? "group/atom cursor-pointer outline-none"
                            : active && !connectMode
                              ? "cursor-help"
                              : "cursor-default"
                      }
                    >
                      <title>
                        {conflict ?? atom}
                        {selected
                          ? " · selected"
                          : enabled
                            ? " · click to select"
                            : " · unavailable for this scope"}
                      </title>
                      <rect
                        x={x - (atom.length * 7 + 4) / 2}
                        y={y - 8}
                        width={atom.length * 7 + 4}
                        height="17"
                        rx="7"
                        fill={mapped ? "transparent" : "white"}
                      />
                      <rect
                        x={x - 15}
                        y={y - 13}
                        width="30"
                        height="26"
                        rx="7"
                        fill={selectedColor}
                        fillOpacity={selected && !mapped ? 0.12 : 0}
                        stroke={
                          !mapped && editable && enabled ? selectedColor : "transparent"
                        }
                        strokeOpacity={selected ? 1 : 0.3}
                        strokeWidth="1.5"
                        className="group-hover/atom:stroke-accent group-focus-visible/atom:stroke-accent"
                      />
                      <text
                        x={x}
                        y={y + 4}
                        textAnchor="middle"
                        fontSize="14"
                        fontFamily="var(--font-mono)"
                        fontWeight={mapped || selected ? 600 : 400}
                        fill={mapped ? "white" : color}
                      >
                        {atom}
                      </text>
                    </g>
                  );
                })}
                {markers.map(({ bead, point: [x, y], label: [labelX, labelY] }) => {
                  const color = beadColor(draft, bead),
                    selected = isSelected(bead);
                  const distance = Math.hypot(labelX + 17 - x, labelY + 10 - y);
                  return (
                    <g key={bead.key}>
                      <line
                        x1={labelX + 17}
                        y1={labelY + 10}
                        x2={x + ((labelX + 17 - x) / distance) * 17}
                        y2={y + ((labelY + 10 - y) / distance) * 17}
                        stroke={color}
                        strokeOpacity=".5"
                        strokeWidth="1"
                        pointerEvents="none"
                      />
                      <g
                        role="button"
                        tabIndex={0}
                        aria-label={`Select ${residue} bead ${bead.beadId} ${bead.name}`}
                        aria-pressed={selected}
                        className="cursor-pointer outline-none focus-visible:stroke-ink"
                        onClick={() => {
                          selectBead(bead);
                        }}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            selectBead(bead);
                          }
                        }}
                      >
                        <title>
                          {bead.beadId} · {bead.name} · click to{" "}
                          {connectMode ? "connect" : "edit"}
                        </title>
                        <rect
                          x={labelX}
                          y={labelY}
                          width="36"
                          height="20"
                          rx="4"
                          fill={selected ? color : "white"}
                          stroke={color}
                          strokeWidth={selected ? 1.5 : 0.8}
                        />
                        <text
                          x={labelX + 18}
                          y={labelY + 13.5}
                          textAnchor="middle"
                          fontSize="10"
                          fontWeight="500"
                          fontFamily="var(--font-mono)"
                          fill={selected ? "white" : color}
                          textLength={bead.beadId.length > 4 ? 30 : undefined}
                          lengthAdjust="spacingAndGlyphs"
                        >
                          {bead.beadId}
                        </text>
                      </g>
                    </g>
                  );
                })}
              </svg>
            </div>
          );
        })}
      </div>
      <div
        className="flex h-14 shrink-0 items-center justify-between gap-2 border-t border-line-soft bg-surface/60 px-3"
        aria-label="Inter-residue connection diagram"
      >
        <div className="min-w-0 text-[10px] text-ink-3">
          <p className="font-medium text-ink">Inter-residue connection</p>
          <p>Residue i → residue i+1</p>
        </div>
        {draft.interResidue.source && draft.interResidue.target ? (
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="rounded border border-accent/30 bg-accent/5 px-2 py-1 text-accent">
              {draft.interResidue.source} <small>i</small>
            </span>
            <span className="text-accent">⇢</span>
            <span className="rounded border border-accent/30 bg-accent/5 px-2 py-1 text-accent">
              {draft.interResidue.target} <small>i+1</small>
            </span>
            <button
              type="button"
              aria-label="Remove 2D inter-residue connection"
              className="cursor-pointer px-1 text-ink-3 hover:text-red-deep"
              onClick={onClearInter}
            >
              ×
            </button>
          </div>
        ) : (
          <span className="text-[10px] text-ink-3">
            {tool === "inter"
              ? "Choose beads on the diagrams"
              : "Choose the Inter-residue tool"}
          </span>
        )}
      </div>
      {!connectMode && conflictHint && conflictHint.key === active?.key && (
        <div role="alert" className={NOTICE_CLASSES}>
          <p>{conflictHint.message} Move that bead or change Scope.</p>
          <Button
            variant="ghost"
            className="mt-2"
            onClick={() => {
              setConflictHint(null);
            }}
          >
            Dismiss
          </Button>
        </div>
      )}
      {scopeHint && scopeHint.key === active?.key && !conflictHint && (
        <div role="alert" className={NOTICE_CLASSES}>
          <p>
            {scopeHint.atom} needs a different mapping scope. Change Scope and keep
            compatible selected atoms.
          </p>
          <div className="mt-2 flex gap-2">
            <Button
              variant="ghost"
              onClick={() => {
                onScopeAtom(scopeHint.scope, scopeHint.atom);
                setScopeHint(null);
              }}
            >
              Use {SCOPES[scopeHint.scope].label} and select {scopeHint.atom}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setScopeHint(null);
              }}
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
