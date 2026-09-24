import { PageHero } from "@/components/layout/PageHero";

export function DocumentationPage() {
  return (
    <PageHero
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
    </PageHero>
  );
}
