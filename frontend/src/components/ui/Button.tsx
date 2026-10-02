import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

import { type ButtonVariant, buttonClasses } from "./buttonStyles";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({
  variant = "primary",
  type = "button",
  className,
  ...props
}: ButtonProps) {
  return (
    <button type={type} className={cn(buttonClasses(variant), className)} {...props} />
  );
}
