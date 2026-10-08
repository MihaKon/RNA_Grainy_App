import { cn } from "@/lib/cn";

interface RnaPolisMarkProps {
  className?: string;
}

// Placeholder until the official RNAPolis wordmark SVG is added.
export function RnaPolisMark({ className }: RnaPolisMarkProps) {
  return (
    <span
      role="img"
      aria-label="RNAPolis"
      className={cn("font-display leading-none tracking-wide", className)}
    >
      RNAPolis
    </span>
  );
}
