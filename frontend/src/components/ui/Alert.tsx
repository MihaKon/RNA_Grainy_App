import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type AlertSeverity = "error" | "info";

interface AlertProps {
  severity: AlertSeverity;
  children: ReactNode;
  className?: string;
}

const SEVERITY_STYLES: Record<AlertSeverity, { edge: string; label: string }> = {
  error: { edge: "border-l-red", label: "text-red-deep" },
  info: { edge: "border-l-blue", label: "text-blue-deep" },
};

export function Alert({ severity, children, className }: AlertProps) {
  const styles = SEVERITY_STYLES[severity];

  return (
    <div
      role={severity === "error" ? "alert" : "status"}
      className={cn(
        "rounded border border-l-[3px] border-line-soft bg-surface px-4 py-3",
        styles.edge,
        className,
      )}
    >
      <p
        className={cn("font-mono text-label tracking-[0.15em] uppercase", styles.label)}
      >
        {severity}
      </p>
      <div className="mt-1 text-sm text-ink">{children}</div>
    </div>
  );
}
