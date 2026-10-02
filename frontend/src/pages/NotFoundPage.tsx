import { Link } from "react-router";

import { PageHero } from "@/components/layout/PageHero";

export function NotFoundPage() {
  return (
    <PageHero
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
    </PageHero>
  );
}
