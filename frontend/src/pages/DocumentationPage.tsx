import { Hero } from "@/components/layout/Hero";

export function DocumentationPage() {
  return (
    <Hero
      eyebrow="Documentation"
      title={
        <>
          Coarse-grained <span className="text-accent">models</span>
        </>
      }
    >
      <p>
        Descriptions, atom mapping rules, and references for every supported
        coarse-grained RNA model.
      </p>
    </Hero>
  );
}
