import { PageHero } from "@/components/layout/PageHero";

export function AboutPage() {
  return (
    <PageHero
      eyebrow="About"
      title={
        <>
          About <span className="text-accent">RNAgrainy</span>
        </>
      }
    >
      <p>
        RNAgrainy is a web application for converting full-atom 3D RNA structures into
        coarse-grained representations.
      </p>
    </PageHero>
  );
}
