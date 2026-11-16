import { type RefObject, useEffect, useEffectEvent } from "react";

export function useDropdownDismiss(
  ref: RefObject<HTMLElement | null>,
  onDismiss: () => void,
) {
  const dismiss = useEffectEvent(onDismiss);

  useEffect(() => {
    const container = ref.current;
    if (!container) return;
    const document = container.ownerDocument;
    let pointerInside = false;
    const handlePointerDown = (event: PointerEvent) => {
      pointerInside = event.composedPath().includes(container);
      if (!pointerInside) dismiss();
    };
    const resetPointer = () => {
      pointerInside = false;
    };
    const handleFocus = (event: FocusEvent) => {
      if (!pointerInside && !event.composedPath().includes(container)) dismiss();
    };
    const handleWindowBlur = () => {
      pointerInside = false;
      dismiss();
    };

    document.addEventListener("pointerdown", handlePointerDown, true);
    document.addEventListener("click", resetPointer, true);
    document.addEventListener("keydown", resetPointer, true);
    document.addEventListener("pointercancel", resetPointer, true);
    document.addEventListener("focusin", handleFocus);
    document.defaultView?.addEventListener("blur", handleWindowBlur);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown, true);
      document.removeEventListener("click", resetPointer, true);
      document.removeEventListener("keydown", resetPointer, true);
      document.removeEventListener("pointercancel", resetPointer, true);
      document.removeEventListener("focusin", handleFocus);
      document.defaultView?.removeEventListener("blur", handleWindowBlur);
    };
  }, [ref]);
}
