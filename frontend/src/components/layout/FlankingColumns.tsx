import { useSyncExternalStore } from "react";

import columnLeftUrl from "@/assets/brand/column-left.png";
import columnRightUrl from "@/assets/brand/column-right.png";

const CONTENT_WIDTH = 768;
const FADE_START_MARGIN = 267;
const FADE_RANGE = 100;
const MAX_OPACITY = 0.4;

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
      className="pointer-events-none absolute inset-x-0 top-6 -z-10 h-[525px] overflow-hidden"
      style={{ opacity: progress * MAX_OPACITY }}
    >
      <img
        src={columnLeftUrl}
        alt=""
        width={238}
        height={315}
        className="absolute top-0 -left-20 h-[315px] w-auto"
      />
      <img
        src={columnRightUrl}
        alt=""
        width={327}
        height={525}
        className="absolute top-0 -right-20 h-[525px] w-auto"
      />
    </div>
  );
}
