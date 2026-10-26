import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "ghost" | "danger" | "text";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "border-accent bg-accent text-white hover:border-accent-hover hover:bg-accent-hover",
  ghost: "border-line-soft bg-white text-ink hover:border-accent hover:text-accent",
  danger: "border-red/40 bg-white text-red-deep hover:border-red hover:bg-red/5",
  text: "text-accent hover:text-accent-hover",
};

function buttonClasses(variant: ButtonVariant): string {
  return cn(
    "inline-flex items-center justify-center rounded transition-colors hover:cursor-pointer disabled:pointer-events-none disabled:opacity-50",
    variant === "text"
      ? "gap-1 font-mono text-label tracking-[0.15em] uppercase focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent"
      : "gap-2 border-[1.5px] px-5 py-2 text-sm font-medium",
    VARIANT_CLASSES[variant],
  );
}

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
