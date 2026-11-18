import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useLocation } from "react-router";

import { getErrorMessage } from "@/api/client";
import { modelsQueryOptions } from "@/api/queries";
import { Hero } from "@/components/layout/Hero";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ModelDocumentationSection } from "@/features/models/ModelDocumentationSection";
import { formatBeadCount } from "@/lib/format";

export function DocumentationPage() {
  const modelsQuery = useQuery(modelsQueryOptions);
  const { hash } = useLocation();
  const models = modelsQuery.data;

  useEffect(() => {
    if (models && hash) {
      document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView();
    }
  }, [models, hash]);

  return (
    <>
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

      <div className="mx-auto max-w-7xl px-4 pb-16 lg:px-8">
        {modelsQuery.isPending && (
          <p role="status" className="text-center eyebrow">
            Loading models…
          </p>
        )}

        {modelsQuery.isError && (
          <Alert severity="error" className="mx-auto max-w-2xl">
            <p className="font-medium">Could not load the model documentation.</p>
            <p className="text-ink-2">{getErrorMessage(modelsQuery.error)}</p>
            <Button
              variant="ghost"
              className="mt-3"
              onClick={() => void modelsQuery.refetch()}
            >
              Try again
            </Button>
          </Alert>
        )}

        {models && (
          <div className="grid gap-8 lg:grid-cols-[16rem_1fr]">
            <nav aria-label="Models" className="lg:sticky lg:top-32 lg:self-start">
              <a
                href="#structure-processing"
                className="mb-5 block border-b border-dashed border-line-soft py-2 text-sm text-accent"
              >
                Structure processing
              </a>
              <h2 className="mb-3 eyebrow">Available models</h2>
              <ul className="grid grid-cols-2 gap-x-4 lg:grid-cols-1">
                {models.map((model) => (
                  <li key={model.id}>
                    <a
                      href={`#${model.id}`}
                      className="flex items-baseline justify-between gap-3 border-b border-dashed border-line-soft py-2 text-sm text-ink-2 transition-colors hover:text-accent"
                    >
                      {model.name}
                      <span className="font-mono text-label text-ink-3">
                        {formatBeadCount(model.beads_per_residue)}
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </nav>

            <div className="flex min-w-0 flex-col gap-8">
              <section
                id="structure-processing"
                className="scroll-mt-32 rounded-md border border-line-soft bg-white p-6"
              >
                <h2 className="font-display text-heading text-ink">
                  Structure processing
                </h2>
                <div className="mt-4 space-y-3 text-sm text-ink-2">
                  <p>
                    PDB and mmCIF inputs are processed for every selected input model
                    and chain. Atoms without alternate-location labels and atoms in
                    alternate location A are retained; other alternate locations are
                    omitted.
                  </p>
                  <p>
                    Modified nucleotides with a supported canonical parent in the input
                    metadata use that parent's CG definition. The CG residue name
                    becomes A, C, G or U; the reference keeps the original name.
                  </p>
                  <p>
                    Only missing atoms required by the selected CG model are estimated.
                    A canonical nucleotide template is fitted to the retained common
                    atoms, and the positions of missing atoms are taken from the fitted
                    template. Existing coordinates are not moved. These estimates are
                    approximate; no energy minimization or full geometry validation is
                    performed.
                  </p>
                  <p>
                    Fitting requires at least three noncollinear reference atoms.
                    Rebuilding the base or sugar ring additionally requires three
                    noncollinear retained atoms in that fragment. If a required
                    reconstruction fails, the entire nucleotide is skipped and its
                    former neighbors are not connected across the resulting gap.
                    Entirely absent nucleotides are not reconstructed.
                  </p>
                  <p>
                    To accommodate unphosphorylated 5′ ends, a completely absent
                    phosphate group in the first supported nucleotide of each chain is
                    not reconstructed. Partial or internal phosphate groups may be
                    estimated. Inter-residue CG connections longer than 8 Å are omitted;
                    this heuristic does not detect every structural break.
                  </p>
                  <p>
                    The results page provides a downloadable conversion report with
                    counts across all selected models, modified-residue mappings,
                    missing and estimated atoms, created and skipped beads, and omitted
                    connections.
                  </p>
                </div>
              </section>
              {models.map((model) => (
                <ModelDocumentationSection key={model.id} model={model} />
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
