import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink } from "react-router";

import { RnaPolisMark } from "@/components/brand/RnaPolisMark";
import { GitHubIcon } from "@/components/icons/GitHubIcon";
import { useScrolled } from "@/hooks/useScrolled";
import { cn } from "@/lib/cn";
import { GITHUB_REPOSITORY_URL, RNAPOLIS_URL } from "@/lib/links";

const SCROLL_SHRINK_THRESHOLD = 40;

const NAV_ITEMS = [
  { to: "/", label: "New model", end: true },
  { to: "/documentation", label: "Documentation", end: false },
  { to: "/about", label: "About", end: false },
] as const;

export function Header() {
  const scrolled = useScrolled(SCROLL_SHRINK_THRESHOLD);
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => {
    setMenuOpen(false);
  };

  return (
    <header className="border-b border-line-soft bg-surface">
      <div
        className={cn(
          "mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 transition-[height] duration-200 lg:px-8",
          scrolled ? "h-14" : "h-20",
        )}
      >
        <div className="flex items-center gap-4">
          <a href={RNAPOLIS_URL} target="_blank" rel="noopener noreferrer">
            <RnaPolisMark
              className={cn("transition-[height]", scrolled ? "h-8" : "h-11")}
            />
          </a>
          <span aria-hidden="true" className="h-8 w-px bg-line-soft" />
          <Link to="/" className="flex flex-col" onClick={closeMenu}>
            <span
              className={cn(
                "font-display text-ink transition-[font-size]",
                scrolled ? "text-heading-compact" : "text-heading",
              )}
            >
              RNAgrainy
            </span>
            {!scrolled && (
              <span className="hidden eyebrow text-[0.5625rem] lg:inline">
                A web server for coarse-graining full-atom 3D RNA structures
              </span>
            )}
          </Link>
        </div>

        <nav aria-label="Main" className="hidden items-center gap-6 lg:flex">
          <NavItems onNavigate={closeMenu} />
          <GitHubLink />
        </nav>

        <button
          type="button"
          className="rounded p-2 text-ink-2 hover:text-accent lg:hidden"
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          onClick={() => {
            setMenuOpen((open) => !open);
          }}
        >
          {menuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </div>

      {menuOpen && (
        <nav
          id="mobile-menu"
          aria-label="Main"
          className="flex flex-col gap-3 border-t border-line-soft px-4 py-4 lg:hidden"
        >
          <NavItems onNavigate={closeMenu} />
          <GitHubLink />
        </nav>
      )}
    </header>
  );
}

function NavItems({ onNavigate }: { onNavigate: () => void }) {
  return NAV_ITEMS.map(({ to, label, end }) => (
    <NavLink
      key={to}
      to={to}
      end={end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "text-sm transition-colors",
          isActive ? "font-medium text-accent" : "text-ink-2 hover:text-accent",
        )
      }
    >
      {label}
    </NavLink>
  ));
}

function GitHubLink() {
  return (
    <a
      href={GITHUB_REPOSITORY_URL}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="RNAgrainy repository on GitHub"
      className="text-red transition-colors hover:text-red-deep"
    >
      <GitHubIcon className="size-6" />
    </a>
  );
}
