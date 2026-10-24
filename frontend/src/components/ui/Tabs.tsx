import { type ReactNode, useId } from "react";

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

export function Tabs<T extends string>({
  label,
  items,
  value,
  onChange,
  panelClassName,
  children,
}: TabsProps<T>) {
  const baseId = useId();
  const tabId = (item: T) => `${baseId}-tab-${item}`;
  const panelId = `${baseId}-panel`;

  return (
    <div>
      <div role="tablist" aria-label={label} className="flex border-b border-line-soft">
        {items.map((item) => {
          const selected = item.value === value;
          return (
            <button
              key={item.value}
              type="button"
              role="tab"
              id={tabId(item.value)}
              aria-selected={selected}
              aria-controls={panelId}
              onClick={() => {
                onChange(item.value);
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
