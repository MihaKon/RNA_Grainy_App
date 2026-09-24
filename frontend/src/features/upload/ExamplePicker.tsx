import { useId } from "react";

import { cn } from "@/lib/cn";

interface ExamplePickerProps {
  presetIds: readonly string[];
  value: string;
  error?: string | undefined;
  onChange: (presetId: string) => void;
}

export function ExamplePicker({
  presetIds,
  value,
  error,
  onChange,
}: ExamplePickerProps) {
  const groupId = useId();
  const labelId = `${groupId}-label`;
  const messageId = `${groupId}-message`;

  return (
    <div className="flex flex-col gap-1.5">
      <span
        id={labelId}
        className="text-sm font-medium tracking-wide text-ink uppercase"
      >
        Example structure
      </span>
      <div
        role="radiogroup"
        aria-labelledby={labelId}
        aria-describedby={messageId}
        className="flex flex-wrap gap-2"
      >
        {presetIds.map((presetId) => (
          <label key={presetId} className="cursor-pointer">
            <input
              type="radio"
              name={groupId}
              value={presetId}
              checked={value === presetId}
              onChange={() => {
                onChange(presetId);
              }}
              className="peer sr-only"
            />
            <span
              className={cn(
                "block rounded border-[1.5px] px-3 py-1.5 font-mono text-sm tracking-wider transition-colors peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent",
                value === presetId
                  ? "border-accent bg-accent/5 text-accent"
                  : "border-line-soft bg-surface text-ink-2 hover:border-accent hover:text-accent",
              )}
            >
              {presetId}
            </span>
          </label>
        ))}
      </div>
      {error ? (
        <p id={messageId} className="text-xs text-red-deep">
          {error}
        </p>
      ) : (
        <p id={messageId} className="text-xs text-ink-3">
          Bundled RNA structures from the PDB, ready to process.
        </p>
      )}
    </div>
  );
}
