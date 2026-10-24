import type { ReactNode } from "react";

import { labelClasses } from "@/components/ui/Field";
import { cn } from "@/lib/cn";

interface ChipGroupProps {
  legend: string;
  hint?: ReactNode;
  children: ReactNode;
}

export function ChipGroup({ legend, hint, children }: ChipGroupProps) {
  return (
    <fieldset className="flex min-w-0 flex-col gap-2">
      <legend className={cn("mb-2", labelClasses)}>{legend}</legend>
      <div className="flex flex-wrap gap-1.5">{children}</div>
      {hint && <p className="text-xs text-ink-3">{hint}</p>}
    </fieldset>
  );
}
