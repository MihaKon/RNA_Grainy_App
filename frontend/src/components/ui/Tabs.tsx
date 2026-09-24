import { type KeyboardEvent, type ReactNode, useId, useRef } from "react";

import { cn } from "@/lib/cn";

export interface TabItem<T extends string> {
  value: T;
  label: string;
}

interface TabsProps<T extends string> {
  label: string;
  items: readonly TabItem<T>[];
  value: T;
  onChange: (value: T) => void;
  panelClassName?: string;
  children: ReactNode;
}

const KEY_OFFSETS: Partial<Record<string, number>> = { ArrowLeft: -1, ArrowRight: 1 };

export function Tabs<T extends string>({
  label,
  items,
  value,
  onChange,
  panelClassName,
  children,
}: TabsProps<T>) {
  const baseId = useId();
  const tabRefs = useRef(new Map<T, HTMLButtonElement>());
  const tabId = (item: T) => `${baseId}-tab-${item}`;
  const panelId = `${baseId}-panel`;

  const selectAt = (index: number) => {
    const count = items.length;
    const item = items[((index % count) + count) % count];
    if (!item) return;
    onChange(item.value);
    tabRefs.current.get(item.value)?.focus();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const offset = KEY_OFFSETS[event.key];
    if (offset !== undefined) {
      selectAt(index + offset);
    } else if (event.key === "Home") {
      selectAt(0);
    } else if (event.key === "End") {
      selectAt(items.length - 1);
    } else {
      return;
    }
    event.preventDefault();
  };

  return (
    <div>
      <div role="tablist" aria-label={label} className="flex border-b border-line-soft">
        {items.map((item, index) => {
          const selected = item.value === value;
          return (
            <button
              key={item.value}
              ref={(element) => {
                if (element) tabRefs.current.set(item.value, element);
                else tabRefs.current.delete(item.value);
              }}
              type="button"
              role="tab"
              id={tabId(item.value)}
              aria-selected={selected}
              aria-controls={panelId}
              tabIndex={selected ? 0 : -1}
              onClick={() => {
                onChange(item.value);
              }}
              onKeyDown={(event) => {
                handleKeyDown(event, index);
              }}
              className={cn(
                "flex-1 px-3 py-2.5 font-mono text-label tracking-[0.15em] uppercase transition-colors",
                selected
                  ? "bg-accent text-white"
                  : "text-ink-2 hover:bg-accent/5 hover:text-accent",
              )}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      <div
        role="tabpanel"
        id={panelId}
        aria-labelledby={tabId(value)}
        className={panelClassName}
      >
        {children}
      </div>
    </div>
  );
}
