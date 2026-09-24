import { useSyncExternalStore } from "react";

import breakingColumnUrl from "@/assets/brand/column-breaking.webp";
import helixColumnUrl from "@/assets/brand/column-helix.webp";

// The guidelines fade the columns in once the side margin next to the content passes a
// threshold, reaching full opacity over the next 100px of margin.
const CONTENT_WIDTH = 768;
const COLUMN_WIDTH = 260;
const FADE_START_MARGIN = 220;
const FADE_RANGE = 100;
const TINT_OPACITY = 0.4;

const COLUMNS = [
  { side: "left", url: helixColumnUrl, aspectRatio: 600 / 1107 },
  { side: "right", url: breakingColumnUrl, aspectRatio: 600 / 993 },
] as const;

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
      className="pointer-events-none absolute inset-x-0 top-0 -z-10 overflow-hidden"
      style={{ height: COLUMN_WIDTH / COLUMNS[0].aspectRatio }}
    >
      {COLUMNS.map(({ side, url, aspectRatio }) => (
        <span
          key={side}
          className="absolute top-0 bg-accent"
          style={{
            [side]: 0,
            width: COLUMN_WIDTH,
            aspectRatio,
            opacity: progress * TINT_OPACITY,
            translate: side === "left" ? "-15% 0" : "15% 0",
            maskImage: `url(${url})`,
            maskSize: "contain",
            maskRepeat: "no-repeat",
          }}
        />
      ))}
    </div>
  );
}
