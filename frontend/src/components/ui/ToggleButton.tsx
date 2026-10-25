import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

const STATE_CLASSES = {
  pressed: "border-accent bg-accent/5 text-accent",
  released:
    "border-line-soft bg-white text-ink-2 hover:border-accent hover:text-accent",
};

function toggleButtonClasses(pressed: boolean): string {
  return cn(
    "inline-flex items-center gap-1.5 rounded border-[1.5px] px-2.5 py-1 font-mono text-label tracking-[0.12em] uppercase transition-colors hover:cursor-pointer disabled:opacity-50",
    pressed ? STATE_CLASSES.pressed : STATE_CLASSES.released,
  );
}

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
      className={cn(toggleButtonClasses(pressed), className)}
      {...props}
    />
  );
}
