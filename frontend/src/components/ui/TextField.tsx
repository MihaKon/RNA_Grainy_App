import { type InputHTMLAttributes, type ReactNode, useId } from "react";

import { cn } from "@/lib/cn";

import { Field, inputClasses } from "./Field";

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  label: ReactNode;
  hint?: ReactNode;
  error?: string | undefined;
}

export function TextField({ label, hint, error, className, ...props }: TextFieldProps) {
  const id = useId();

  return (
    <Field id={id} label={label} hint={hint} error={error}>
      {({ inputId, describedBy, invalid }) => (
        <input
          id={inputId}
          aria-describedby={describedBy}
          aria-invalid={invalid || undefined}
          className={cn(inputClasses, className)}
          {...props}
        />
      )}
    </Field>
  );
}
