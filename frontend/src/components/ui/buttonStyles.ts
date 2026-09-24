import { cn } from "@/lib/cn";

export type ButtonVariant = "primary" | "ghost";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "border-accent bg-accent text-white hover:border-accent-hover hover:bg-accent-hover",
  ghost: "border-line-soft bg-white text-ink hover:border-accent hover:text-accent",
};

export function buttonClasses(variant: ButtonVariant = "primary"): string {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded border-[1.5px] px-5 py-2 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
    VARIANT_CLASSES[variant],
  );
}
