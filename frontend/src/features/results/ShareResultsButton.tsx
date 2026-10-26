import { Check, Share2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";

interface ShareResultsButtonProps {
  workspaceId: string;
}

export function ShareResultsButton({ workspaceId }: ShareResultsButtonProps) {
  const { status, copy } = useCopyToClipboard();
  const url = new URL(
    `/results/${encodeURIComponent(workspaceId)}/`,
    window.location.origin,
  ).href;

  return (
    <div className="flex max-w-full flex-col items-start gap-2 lg:items-end">
      <Button
        variant="text"
        disabled={status === "copying"}
        onClick={() => {
          void copy(url);
        }}
      >
        {status === "copied" ? (
          <Check aria-hidden="true" className="size-3" />
        ) : (
          <Share2 aria-hidden="true" className="size-3" />
        )}

        {status === "copied"
          ? "Link copied"
          : status === "copying"
            ? "Copying…"
            : "Share results"}
      </Button>

      <span role="status" className="sr-only">
        {status === "copied" ? "Result link copied to clipboard." : ""}
      </span>

      {status === "error" && (
        <div className="w-full max-w-sm">
          <p role="alert" className="mb-1 text-xs text-ink-2">
            Could not copy automatically. Select and copy the link:
          </p>
          <input
            aria-label="Result link"
            readOnly
            value={url}
            onFocus={(event) => {
              event.currentTarget.select();
            }}
            className="w-full min-w-0 rounded border border-line-soft bg-white px-3 py-2 text-sm text-ink"
          />
        </div>
      )}
    </div>
  );
}
