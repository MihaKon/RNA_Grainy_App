import type { ReactNode } from "react";

export interface FieldIds {
  inputId: string;
  describedBy: string | undefined;
  invalid: boolean;
}

interface FieldProps {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
  error?: string | undefined;
  children: (ids: FieldIds) => ReactNode;
}

export const inputClasses =
  "w-full rounded border-[1.5px] border-line-soft bg-surface px-3 py-2 font-mono text-sm text-ink transition-colors placeholder:text-ink-3/70 focus:border-accent focus:outline-none aria-invalid:border-red disabled:opacity-60";

export function Field({ id, label, hint, error, children }: FieldProps) {
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [errorId, hintId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="text-sm font-medium tracking-wide text-ink uppercase"
      >
        {label}
      </label>
      {children({ inputId: id, describedBy, invalid: Boolean(error) })}
      {error && (
        <p id={errorId} className="text-xs text-red-deep">
          {error}
        </p>
      )}
      {hint && (
        <p id={hintId} className="text-xs text-ink-3">
          {hint}
        </p>
      )}
    </div>
  );
}
