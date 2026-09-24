import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";

interface DisclosureProps {
  title: string;
  children: ReactNode;
}

export function Disclosure({ title, children }: DisclosureProps) {
  return (
    <details className="group rounded-md border border-line-soft bg-white">
      <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 [&::-webkit-details-marker]:hidden">
        <span className="eyebrow">{title}</span>
        <ChevronDown
          aria-hidden="true"
          className="size-4 text-ink-3 transition-transform group-open:rotate-180"
        />
      </summary>
      <div className="border-t border-dashed border-line-soft px-5 py-4">
        {children}
      </div>
    </details>
  );
}
