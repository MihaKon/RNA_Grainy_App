import horizontalWhiteUrl from "@/assets/brand/rnapolis-horizontal-white.png";
import stackedBlueUrl from "@/assets/brand/rnapolis-stacked.png";
import { cn } from "@/lib/cn";

const LOGOS = {
  "stacked-blue": { src: stackedBlueUrl, width: 582, height: 505 },
  "horizontal-white": { src: horizontalWhiteUrl, width: 479, height: 97 },
} as const;

interface RnaPolisMarkProps {
  variant?: keyof typeof LOGOS;
  className?: string;
}

export function RnaPolisMark({
  variant = "stacked-blue",
  className,
}: RnaPolisMarkProps) {
  const { src, width, height } = LOGOS[variant];

  return (
    <img
      src={src}
      alt="RNAPolis"
      width={width}
      height={height}
      className={cn("w-auto", className)}
    />
  );
}
