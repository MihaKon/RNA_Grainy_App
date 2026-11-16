import { Trash2 } from "lucide-react";
import type { Dispatch } from "react";

import { Button } from "@/components/ui/Button";
import { SelectField } from "@/components/ui/SelectField";
import { TextField } from "@/components/ui/TextField";
import { ToggleButton } from "@/components/ui/ToggleButton";

import {
  BEAD_SCOPES,
  BEAD_STRATEGIES,
  type BeadStrategy,
  SCOPES,
  STRATEGY_LABELS,
} from "./atoms";
import { ChipGroup } from "./ChipGroup";
import {
  atomSelection,
  type BeadDraft,
  type DraftAction,
  type ModelDraft,
  positionConflict,
} from "./modelDraft";

interface BeadEditorProps {
  draft: ModelDraft;
  bead: BeadDraft;
  issues: readonly string[] | undefined;
  dispatch: Dispatch<DraftAction>;
}

const STRATEGY_HINTS: Record<BeadStrategy, string> = {
  direct: "Direct mapping places the bead on exactly one atom.",
  center_of_mass: "The bead is placed at the center of mass of the selected atoms.",
  geometric_center: "The bead is placed at the geometric center of the selected atoms.",
};

export function BeadEditor({ draft, bead, issues, dispatch }: BeadEditorProps) {
  const scopeAtoms = SCOPES[bead.scope].atoms;
  const atomChoices = [
    ...scopeAtoms,
    ...bead.atoms.filter((atom) => !scopeAtoms.includes(atom)),
  ];
  const { key } = bead;

  return (
    <article
      aria-label={`Bead ${bead.beadId || "without ID"}`}
      className="relative flex flex-col gap-3 bg-white"
    >
      <div className="grid grid-cols-2 gap-2 [&>div:last-child]:col-span-2">
        <TextField
          label="Bead ID"
          value={bead.beadId}
          maxLength={5}
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => {
            dispatch({ type: "renameBead", key, beadId: event.target.value });
          }}
        />
        <TextField
          label="Bead name"
          value={bead.name}
          maxLength={5}
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => {
            dispatch({ type: "updateBead", key, patch: { name: event.target.value } });
          }}
        />
        <SelectField
          label="Strategy"
          value={bead.strategy}
          onChange={(event) => {
            const strategy = BEAD_STRATEGIES.find(
              (value) => value === event.target.value,
            );
            if (strategy) dispatch({ type: "setBeadStrategy", key, strategy });
          }}
        >
          {BEAD_STRATEGIES.map((strategy) => (
            <option
              key={strategy}
              value={strategy}
              disabled={
                !!positionConflict(draft, {
                  ...bead,
                  strategy,
                  atoms: strategy === "direct" ? bead.atoms.slice(0, 1) : bead.atoms,
                })
              }
            >
              {STRATEGY_LABELS[strategy]}
            </option>
          ))}
        </SelectField>
      </div>

      <TextField
        label="Bead description"
        value={bead.description}
        placeholder="e.g. Phosphate P atom"
        onChange={(event) => {
          dispatch({
            type: "updateBead",
            key,
            patch: { description: event.target.value },
          });
        }}
      />
      <ChipGroup legend="Scope">
        {BEAD_SCOPES.map((scope) => (
          <ToggleButton
            key={scope}
            pressed={bead.scope === scope}
            onClick={() => {
              dispatch({ type: "setBeadScope", key, scope });
            }}
          >
            {SCOPES[scope].label}
          </ToggleButton>
        ))}
      </ChipGroup>

      <ChipGroup legend="Atoms" hint={STRATEGY_HINTS[bead.strategy]}>
        {atomChoices.map((atom) => {
          const conflict = positionConflict(draft, atomSelection(bead, atom));
          return (
            <ToggleButton
              key={atom}
              pressed={bead.atoms.includes(atom)}
              disabled={!!conflict}
              title={conflict}
              className="normal-case"
              onClick={() => {
                dispatch({ type: "toggleAtom", key, atom });
              }}
            >
              {atom}
            </ToggleButton>
          );
        })}
        {bead.atoms.length === 0 && (
          <p className="text-xs text-ink-3">
            Select atoms in the diagrams or this list.
          </p>
        )}
      </ChipGroup>

      {issues && (
        <ul className="flex flex-col gap-1 text-xs text-red-deep">
          {issues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      )}
      <Button
        variant="danger"
        aria-label={`Remove bead ${bead.beadId}`}
        onClick={() => {
          dispatch({ type: "removeBead", key });
        }}
      >
        <Trash2 aria-hidden="true" className="size-4" /> Remove bead
      </Button>
    </article>
  );
}
