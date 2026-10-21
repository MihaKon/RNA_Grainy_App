import { type ReactNode, useEffect, useRef } from "react";
import { createPortal } from "react-dom";

interface DrawerProps {
  open: boolean;
  labelledBy: string;
  onClose: () => void;
  children: ReactNode;
}

export function Drawer({ open, labelledBy, onClose, children }: DrawerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  // Portaled out of any surrounding form: Enter in a drawer field would submit it.
  return createPortal(
    <dialog
      ref={dialogRef}
      aria-labelledby={labelledBy}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      className="m-0 h-auto max-h-[92dvh] w-full max-w-none overflow-y-auto border-b border-line-soft bg-surface p-0 text-ink-2 backdrop:bg-ink/45"
    >
      {open && children}
    </dialog>,
    document.body,
  );
}
