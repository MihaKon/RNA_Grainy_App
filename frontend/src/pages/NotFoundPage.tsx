import { Link } from "react-router";

import { Hero } from "@/components/layout/Hero";

export function NotFoundPage() {
  return (
    <Hero
      eyebrow="Error 404"
      title={
        <>
          Page <span className="text-accent">not found</span>
        </>
      }
    >
      <Link to="/" className="text-accent hover:text-accent-hover">
        ← Back to RNAgrainy
      </Link>
    </Hero>
  );
}
