import { PageHero } from "@/components/layout/PageHero";
import { GITHUB_REPOSITORY_URL } from "@/lib/links";

interface Author {
  name: string;
  initials: string;
  role: string;
  affiliations: number[];
  url: string;
}

const AUTHORS: readonly Author[] = [
  {
    name: "Sergiusz Urbaniak",
    initials: "SU",
    role: "Development",
    affiliations: [1],
    url: "https://github.com/serguppp",
  },
  {
    name: "Michał Konon",
    initials: "MK",
    role: "Development",
    affiliations: [1],
    url: "https://github.com/mihakon",
  },
  {
    name: "Marta Szachniuk",
    initials: "MS",
    role: "Scientific supervision",
    affiliations: [1, 2],
    url: "https://www.cs.put.poznan.pl/mszachniuk/site/",
  },
];

const AFFILIATIONS = [
  "Institute of Computing Science, Poznan University of Technology, Poland",
  "Institute of Bioorganic Chemistry, Polish Academy of Sciences, Poznan, Poland",
] as const;

export function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="About"
        title={
          <>
            About <span className="text-accent">RNAgrainy</span>
          </>
        }
      />

      <div className="mx-auto flex max-w-3xl flex-col gap-12 px-4 pb-16">
        <section aria-labelledby="about-heading" className="flex flex-col gap-4">
          <h2 id="about-heading" className="eyebrow">
            The application
          </h2>
          <p>
            RNAgrainy is a web application for converting full-atom 3D RNA structures
            into coarse-grained representations. It supports multiple coarse-grained
            models with different atom mapping rules and levels of structural detail,
            and lets you define your own.
          </p>
          <p>
            The application provides tools for uploading, processing, visualizing, and
            downloading RNA structures, and facilitates the comparison of different
            coarse-grained representations. RNAgrainy is intended to support research
            involving RNA structure analysis, modelling, and simulation.
          </p>
          <a
            href={GITHUB_REPOSITORY_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="group mt-2 flex items-center gap-4 border-t border-line-soft pt-4"
          >
            <span className="rounded border border-blue/30 bg-blue/5 px-2 py-0.5 font-mono text-label tracking-[0.15em] text-blue-deep uppercase">
              GitHub
            </span>
            <span className="text-sm text-ink-2 group-hover:text-accent">
              Source code of RNAgrainy ↗
            </span>
          </a>
        </section>

        <section aria-labelledby="authors-heading" className="flex flex-col gap-6">
          <h2 id="authors-heading" className="eyebrow">
            Authors
          </h2>
          <ul className="grid gap-6 lg:grid-cols-3">
            {AUTHORS.map((author) => (
              <li
                key={author.name}
                className="flex flex-col items-center gap-2 text-center"
              >
                <span
                  aria-hidden="true"
                  className="flex size-16 items-center justify-center rounded-full bg-blue font-display text-2xl text-white"
                >
                  {author.initials}
                </span>
                <a
                  href={author.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-semibold text-ink hover:text-accent"
                >
                  {author.name}
                  <sup className="ml-0.5 font-mono font-normal text-ink-3">
                    {author.affiliations.join(",")}
                  </sup>
                </a>
                <span className="font-mono text-label tracking-[0.15em] text-ink-3 uppercase">
                  {author.role}
                </span>
              </li>
            ))}
          </ul>
          <ol className="flex flex-col gap-1 border-t border-dashed border-line-soft pt-4 text-xs text-ink-3">
            {AFFILIATIONS.map((affiliation, index) => (
              <li key={affiliation}>
                <sup className="mr-1 font-mono">{index + 1}</sup>
                {affiliation}
              </li>
            ))}
          </ol>
        </section>
      </div>
    </>
  );
}
