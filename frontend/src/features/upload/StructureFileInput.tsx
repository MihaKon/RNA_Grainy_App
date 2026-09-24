import { FileUp, X } from "lucide-react";
import { type ChangeEvent, type DragEvent, useId, useRef, useState } from "react";

import { cn } from "@/lib/cn";
import { formatBytes } from "@/lib/format";

interface StructureFileInputProps {
  file: File | null;
  accept: string;
  hint: string;
  error?: string | undefined;
  onChange: (file: File | null) => void;
}

export function StructureFileInput({
  file,
  accept,
  hint,
  error,
  onChange,
}: StructureFileInputProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const describedBy = error ? `${inputId}-error` : `${inputId}-hint`;

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.files?.[0] ?? null);
  };

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile) onChange(droppedFile);
  };

  const clearFile = () => {
    if (inputRef.current) inputRef.current.value = "";
    onChange(null);
  };

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium tracking-wide text-ink uppercase">
        Structure file
      </span>
      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept={accept}
        aria-describedby={describedBy}
        aria-invalid={Boolean(error) || undefined}
        onChange={handleChange}
        className="peer sr-only"
      />

      {file ? (
        <div className="flex items-center justify-between gap-3 rounded border-[1.5px] border-accent bg-surface px-3 py-2.5">
          <div className="min-w-0">
            <p className="truncate font-mono text-sm text-ink">{file.name}</p>
            <p className="font-mono text-label text-ink-3">{formatBytes(file.size)}</p>
          </div>
          <button
            type="button"
            onClick={clearFile}
            aria-label={`Remove ${file.name}`}
            className="rounded p-1.5 text-ink-3 transition-colors hover:text-red-deep"
          >
            <X className="size-4" />
          </button>
        </div>
      ) : (
        <label
          htmlFor={inputId}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => {
            setDragging(false);
          }}
          onDrop={handleDrop}
          className={cn(
            "flex cursor-pointer flex-col items-center gap-1.5 rounded border-[1.5px] border-dashed bg-surface px-4 py-6 text-center transition-colors peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent hover:border-accent",
            dragging ? "border-accent bg-accent/5" : "border-line-soft",
            error && "border-red",
          )}
        >
          <FileUp aria-hidden="true" className="size-5 text-accent" />
          <span className="text-sm text-ink">
            <span className="font-medium text-accent">Choose a file</span> or drop it
            here
          </span>
        </label>
      )}

      {error ? (
        <p id={`${inputId}-error`} className="text-xs text-red-deep">
          {error}
        </p>
      ) : (
        <p id={`${inputId}-hint`} className="text-xs text-ink-3">
          {hint}
        </p>
      )}
    </div>
  );
}
