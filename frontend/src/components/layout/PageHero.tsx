import type { ReactNode } from "react";

interface PageHeroProps {
  eyebrow?: string;
  title: ReactNode;
  children?: ReactNode;
}

export function PageHero({ eyebrow, title, children }: PageHeroProps) {
  return (
    <section className="mx-auto max-w-3xl px-4 pt-16 pb-10 text-center">
      {eyebrow && <p className="mb-3 eyebrow">{eyebrow}</p>}
      <h1 className="font-display text-hero-compact text-ink lg:text-hero">{title}</h1>
      {children && <div className="mx-auto mt-4 max-w-xl">{children}</div>}
    </section>
  );
}
