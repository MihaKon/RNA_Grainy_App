import { ChevronDown } from "lucide-react";
import { type ReactNode, type SelectHTMLAttributes, useId } from "react";

import { cn } from "@/lib/cn";

import { Field, inputClasses } from "./Field";

interface SelectFieldProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "id"> {
  label: ReactNode;
  hint?: ReactNode;
  error?: string | undefined;
}

export function SelectField({
  label,
  hint,
  error,
  className,
  children,
  ...props
}: SelectFieldProps) {
  const id = useId();

  return (
    <Field id={id} label={label} hint={hint} error={error}>
      {({ inputId, describedBy, invalid }) => (
        <div className="relative">
          <select
            id={inputId}
            aria-describedby={describedBy}
            aria-invalid={invalid || undefined}
            className={cn(
              inputClasses,
              "cursor-pointer appearance-none pr-9",
              className,
            )}
            {...props}
          >
            {children}
          </select>
          <ChevronDown
            aria-hidden="true"
            className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-ink-3"
          />
        </div>
      )}
    </Field>
  );
}
