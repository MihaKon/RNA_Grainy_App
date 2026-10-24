import { useSyncExternalStore } from "react";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("scroll", onChange, { passive: true });
  return () => {
    window.removeEventListener("scroll", onChange);
  };
}

export function useScrolled(threshold: number): boolean {
  return useSyncExternalStore(
    subscribe,
    () => window.scrollY > threshold,
    () => false,
  );
}
