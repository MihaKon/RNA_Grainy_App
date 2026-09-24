import { useSyncExternalStore } from "react";

import columnUrl from "@/assets/brand/column-helix.webp";

// The guidelines fade the columns in once the side margin next to the content passes a
// threshold, reaching full opacity over the next 100px of margin.
const CONTENT_WIDTH = 768;
const COLUMN_WIDTH = 330;
const COLUMN_ASPECT_RATIO = 600 / 1107;
const FADE_START_MARGIN = 220;
const FADE_RANGE = 100;
const TINT_OPACITY = 0.4;

// Keeps the capital and the top of the shaft, cut diagonally just above the helix and
// descending towards the page edge.
const SHAFT_CUT = "polygon(0 0, 100% 0, 100% 31%, 80% 32.5%, 22% 51.5%, 0 51.5%)";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("resize", onChange);
  return () => {
    window.removeEventListener("resize", onChange);
  };
}

function useFadeProgress(): number {
  return useSyncExternalStore(
    subscribe,
    () => {
      const margin = (window.innerWidth - CONTENT_WIDTH) / 2;
      return Math.min(Math.max((margin - FADE_START_MARGIN) / FADE_RANGE, 0), 1);
    },
    () => 0,
  );
}

export function FlankingColumns() {
  const progress = useFadeProgress();
  if (progress === 0) return null;

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-x-0 top-6 -z-10 overflow-hidden"
      style={{ height: (COLUMN_WIDTH / COLUMN_ASPECT_RATIO) * 0.52 }}
    >
      {(["left", "right"] as const).map((side) => (
        <span
          key={side}
          className="absolute top-0 bg-accent"
          style={{
            [side]: 0,
            width: COLUMN_WIDTH,
            aspectRatio: COLUMN_ASPECT_RATIO,
            opacity: progress * TINT_OPACITY,
            translate: side === "left" ? "-25% 0" : "25% 0",
            scale: side === "right" ? "-1 1" : undefined,
            clipPath: SHAFT_CUT,
            maskImage: `url(${columnUrl})`,
            maskSize: "contain",
            maskRepeat: "no-repeat",
          }}
        />
      ))}
    </div>
  );
}
