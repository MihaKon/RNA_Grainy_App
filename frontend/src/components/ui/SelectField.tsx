import { ChevronDown } from "lucide-react";
import { type ReactNode, type SelectHTMLAttributes, useId } from "react";

import { cn } from "@/lib/cn";

import { Field, inputClasses } from "./Field";

interface SelectFieldProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "id"> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: string | undefined;
  inline?: boolean;
}

export function SelectField({
  label,
  hint,
  error,
  className,
  children,
  inline = false,
  ...props
}: SelectFieldProps) {
  const id = useId();

  return (
    <Field id={id} label={label} hint={hint} error={error} inline={inline}>
      {({ inputId, describedBy, invalid }) => (
        <div className="relative">
          <select
            id={inputId}
            aria-describedby={describedBy}
            aria-invalid={invalid || undefined}
            className={cn(
              inputClasses,
              "peer cursor-pointer appearance-none pr-9",
              inline && "h-7 w-auto! py-0! pr-7! pl-2! text-xs!",
              className,
            )}
            {...props}
          >
            {children}
          </select>
          <ChevronDown
            aria-hidden="true"
            className={cn(
              "pointer-events-none absolute top-1/2 -translate-y-1/2 text-ink-3 transition-transform peer-[:open]:rotate-180",
              inline ? "right-2 size-3.5" : "right-3 size-4",
            )}
          />
        </div>
      )}
    </Field>
  );
}
