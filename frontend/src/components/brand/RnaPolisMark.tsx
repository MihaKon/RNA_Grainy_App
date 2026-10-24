import logoUrl from "@/assets/brand/rnapolis-stacked.png";
import { cn } from "@/lib/cn";

type RnaPolisColorway = "blue" | "white";

interface RnaPolisMarkProps {
  colorway?: RnaPolisColorway;
  className?: string;
}

export function RnaPolisMark({ colorway = "blue", className }: RnaPolisMarkProps) {
  return (
    <img
      src={logoUrl}
      alt="RNAPolis"
      width={582}
      height={505}
      className={cn("w-auto", colorway === "white" && "brightness-0 invert", className)}
    />
  );
}
