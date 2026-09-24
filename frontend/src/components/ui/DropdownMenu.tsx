import { ChevronDown } from "lucide-react";
import {
  type KeyboardEvent,
  type ReactNode,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

import { cn } from "@/lib/cn";

import { type ButtonVariant, buttonClasses } from "./buttonStyles";

export interface DropdownMenuItem {
  id: string;
  label: string;
  description?: string;
  disabled?: boolean;
  onSelect: () => void;
}

interface DropdownMenuProps {
  label: ReactNode;
  items: readonly DropdownMenuItem[];
  variant?: ButtonVariant;
  disabled?: boolean;
}

export function DropdownMenu({
  label,
  items,
  variant = "primary",
  disabled = false,
}: DropdownMenuProps) {
  const menuId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const open = activeIndex !== null;

  const enabledIndexes = items.flatMap((item, index) => (item.disabled ? [] : [index]));

  useEffect(() => {
    if (activeIndex !== null) itemRefs.current[activeIndex]?.focus();
  }, [activeIndex]);

  useEffect(() => {
    if (!open) return;
    const closeOnOutsidePointer = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setActiveIndex(null);
    };
    document.addEventListener("pointerdown", closeOnOutsidePointer);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutsidePointer);
    };
  }, [open]);

  const openAt = (position: "first" | "last") => {
    const index = position === "first" ? enabledIndexes[0] : enabledIndexes.at(-1);
    if (index !== undefined) setActiveIndex(index);
  };

  const close = (restoreFocus: boolean) => {
    setActiveIndex(null);
    if (restoreFocus) buttonRef.current?.focus();
  };

  const moveFocus = (offset: number) => {
    if (activeIndex === null || enabledIndexes.length === 0) return;
    const current = enabledIndexes.indexOf(activeIndex);
    const next = (current + offset + enabledIndexes.length) % enabledIndexes.length;
    setActiveIndex(enabledIndexes[next] ?? null);
  };

  const handleButtonKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      openAt(event.key === "ArrowDown" ? "first" : "last");
    }
  };

  const handleMenuKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const actions: Partial<Record<string, () => void>> = {
      ArrowDown: () => {
        moveFocus(1);
      },
      ArrowUp: () => {
        moveFocus(-1);
      },
      Home: () => {
        openAt("first");
      },
      End: () => {
        openAt("last");
      },
      Escape: () => {
        close(true);
      },
      Tab: () => {
        close(false);
      },
    };
    const action = actions[event.key];
    if (!action) return;
    if (event.key !== "Tab") event.preventDefault();
    action();
  };

  return (
    <div ref={containerRef} className="relative">
      <button
        ref={buttonRef}
        type="button"
        disabled={disabled}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => {
          if (open) close(false);
          else openAt("first");
        }}
        onKeyDown={handleButtonKeyDown}
        className={buttonClasses(variant)}
      >
        {label}
        <ChevronDown
          aria-hidden="true"
          className={cn("size-4 transition-transform", open && "rotate-180")}
        />
      </button>

      {open && (
        <div
          id={menuId}
          role="menu"
          onKeyDown={handleMenuKeyDown}
          className="absolute right-0 z-20 mt-2 min-w-56 rounded-md border border-line-soft bg-white py-1"
        >
          {items.map((item, index) => (
            <button
              key={item.id}
              ref={(element) => {
                itemRefs.current[index] = element;
              }}
              type="button"
              role="menuitem"
              tabIndex={-1}
              aria-disabled={item.disabled}
              onClick={() => {
                if (item.disabled) return;
                item.onSelect();
                close(true);
              }}
              className={cn(
                "flex w-full flex-col items-start px-4 py-2 text-left focus:outline-none",
                item.disabled
                  ? "cursor-not-allowed opacity-50"
                  : "hover:bg-accent/5 focus-visible:bg-accent/5",
              )}
            >
              <span className="text-sm font-medium text-ink">{item.label}</span>
              {item.description && (
                <span className="font-mono text-label text-ink-3">
                  {item.description}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
