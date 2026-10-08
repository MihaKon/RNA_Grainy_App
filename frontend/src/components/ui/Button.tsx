import type { AnchorHTMLAttributes, ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "ghost";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "border-accent bg-accent text-white hover:border-accent-hover hover:bg-accent-hover",
  ghost: "border-line-soft bg-white text-ink hover:border-accent hover:text-accent",
};

function buttonClasses(variant: ButtonVariant): string {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded border-[1.5px] px-5 py-2 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
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

interface DownloadButtonProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  download: string;
  variant?: ButtonVariant;
}

export function DownloadButton({
  variant = "primary",
  className,
  ...props
}: DownloadButtonProps) {
  return <a className={cn(buttonClasses(variant), className)} {...props} />;
}
