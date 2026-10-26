import { useState } from "react";

type CopyStatus = "idle" | "copying" | "copied" | "error";

export function useCopyToClipboard() {
  const [status, setStatus] = useState<CopyStatus>("idle");

  async function copy(text: string) {
    setStatus("copying");

    try {
      if (!("clipboard" in navigator)) {
        throw new Error("Clipboard unavailable");
      }

      await navigator.clipboard.writeText(text);
      setStatus("copied");
    } catch {
      setStatus("error");
    }
  }

  return { status, copy };
}
