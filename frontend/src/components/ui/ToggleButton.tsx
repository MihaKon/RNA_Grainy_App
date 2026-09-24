import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

interface ToggleButtonProps extends Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "aria-pressed"
> {
  pressed: boolean;
}

export function ToggleButton({ pressed, className, ...props }: ToggleButtonProps) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      className={cn(
        "inline-flex items-center gap-1.5 rounded border-[1.5px] px-2.5 py-1 font-mono text-label tracking-[0.12em] uppercase transition-colors disabled:opacity-50",
        pressed
          ? "border-accent bg-accent/5 text-accent"
          : "border-line-soft bg-white text-ink-2 hover:border-accent hover:text-accent",
        className,
      )}
      {...props}
    />
  );
}
