import { X } from "lucide-react";
import type { Dispatch } from "react";

import { SelectField } from "@/components/ui/SelectField";
import { TextField } from "@/components/ui/TextField";
import { ToggleButton } from "@/components/ui/ToggleButton";

import {
  BEAD_SCOPES,
  BEAD_STRATEGIES,
  type BeadStrategy,
  SCOPE_ATOMS,
  SCOPE_LABELS,
  STRATEGY_LABELS,
} from "./atoms";
import { ChipGroup } from "./ChipGroup";
import type { BeadDraft, DraftAction } from "./modelDraft";

interface BeadEditorProps {
  bead: BeadDraft;
  issues: readonly string[] | undefined;
  dispatch: Dispatch<DraftAction>;
}

const STRATEGY_HINTS: Record<BeadStrategy, string> = {
  direct: "Direct mapping places the bead on exactly one atom.",
  center_of_mass: "The bead is placed at the center of mass of the selected atoms.",
  geometric_center: "The bead is placed at the geometric center of the selected atoms.",
};

export function BeadEditor({ bead, issues, dispatch }: BeadEditorProps) {
  const { key } = bead;

  return (
    <article
      aria-label={`Bead ${bead.beadId || "without ID"}`}
      className="relative flex flex-col gap-5 rounded-md border border-line-soft bg-white p-5"
    >
      <button
        type="button"
        onClick={() => {
          dispatch({ type: "removeBead", key });
        }}
        aria-label={`Remove bead ${bead.beadId}`}
        className="absolute top-3 right-3 rounded p-1.5 text-ink-3 transition-colors hover:text-red-deep"
      >
        <X className="size-4" />
      </button>

      <div className="grid gap-4 pr-8 lg:grid-cols-3">
        <TextField
          label="Bead ID"
          value={bead.beadId}
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => {
            dispatch({ type: "renameBead", key, beadId: event.target.value });
          }}
        />
        <TextField
          label="Bead name"
          value={bead.name}
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
            <option key={strategy} value={strategy}>
              {STRATEGY_LABELS[strategy]}
            </option>
          ))}
        </SelectField>
      </div>

      <TextField
        label="Description"
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

      <ChipGroup legend="Applies to">
        {BEAD_SCOPES.map((scope) => (
          <ToggleButton
            key={scope}
            pressed={bead.scope === scope}
            onClick={() => {
              dispatch({ type: "setBeadScope", key, scope });
            }}
          >
            {SCOPE_LABELS[scope]}
          </ToggleButton>
        ))}
      </ChipGroup>

      <ChipGroup legend="Atoms" hint={STRATEGY_HINTS[bead.strategy]}>
        {SCOPE_ATOMS[bead.scope].map((atom) => (
          <ToggleButton
            key={atom}
            pressed={bead.atoms.includes(atom)}
            className="normal-case"
            onClick={() => {
              dispatch({ type: "toggleAtom", key, atom });
            }}
          >
            {atom}
          </ToggleButton>
        ))}
      </ChipGroup>

      {issues && (
        <ul className="flex flex-col gap-1 text-xs text-red-deep">
          {issues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      )}
    </article>
  );
}
