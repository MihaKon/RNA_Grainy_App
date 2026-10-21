import type { ReactNode } from "react";

interface ChipGroupProps {
  legend: string;
  hint?: ReactNode;
  children: ReactNode;
}

export function ChipGroup({ legend, hint, children }: ChipGroupProps) {
  return (
    <fieldset className="flex min-w-0 flex-col gap-2">
      <legend className="mb-2 text-sm font-medium tracking-wide text-ink uppercase">
        {legend}
      </legend>
      <div className="flex flex-wrap gap-1.5">{children}</div>
      {hint && <p className="text-xs text-ink-3">{hint}</p>}
    </fieldset>
  );
}
