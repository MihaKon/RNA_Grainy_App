import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useLocation } from "react-router";

import { getErrorMessage } from "@/api/client";
import { modelsQueryOptions } from "@/api/queries";
import { PageHero } from "@/components/layout/PageHero";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ModelDocumentationSection } from "@/features/models/ModelDocumentationSection";
import { formatBeadCount } from "@/lib/format";

export function DocumentationPage() {
  const modelsQuery = useQuery(modelsQueryOptions);
  const { hash } = useLocation();
  const models = modelsQuery.data;

  // The sections render after the models load, so the browser cannot scroll to the hash itself.
  useEffect(() => {
    if (models && hash) {
      document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView();
    }
  }, [models, hash]);

  return (
    <>
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
