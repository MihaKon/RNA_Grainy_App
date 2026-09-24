import { Link } from "react-router";

import { RnaPolisMark } from "@/components/brand/RnaPolisMark";
import { GITHUB_REPOSITORY_URL } from "@/lib/links";

export function SiteFooter() {
  return (
    <footer className="bg-blue-ink text-white/80">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-10 lg:grid-cols-[1fr_auto] lg:px-8">
        <div className="max-w-md">
          <p className="eyebrow text-white/60">RNAgrainy is part of</p>
          <RnaPolisMark colorway="white" className="mt-3 h-14" />
          <p className="mt-4 text-sm">
            A platform of computational tools for RNA structure research, maintained at
            the Institute of Computing Science, Poznan University of Technology, and the
            Department of Structural Bioinformatics, IBCH PAS.
          </p>
        </div>

        <nav aria-label="Resources" className="flex flex-col gap-2 text-sm">
          <p className="eyebrow text-white/60">Resources</p>
          <Link to="/documentation" className="hover:text-white">
            Documentation
          </Link>
          <Link to="/about" className="hover:text-white">
            About
          </Link>
          <a
            href={GITHUB_REPOSITORY_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white"
          >
            GitHub ↗
          </a>
        </nav>
      </div>

      <div className="border-t border-white/10">
        <p className="mx-auto max-w-7xl px-4 py-4 font-mono text-label tracking-[0.15em] text-white/50 uppercase lg:px-8">
          © {new Date().getFullYear()} · RNAgrainy · Poznan University of Technology
        </p>
      </div>
    </footer>
  );
}
