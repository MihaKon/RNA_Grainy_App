import type { ModelDocumentation } from "@/api/types";
import { formatBeadsPerResidue } from "@/lib/format";

import { AtomMappingTable } from "./AtomMappingTable";
import { ModelDescription } from "./ModelDescription";
import { ModelImage } from "./ModelImage";

export function ModelDocumentationSection({ model }: { model: ModelDocumentation }) {
  const headingId = `${model.id}-heading`;

  return (
    <section
      id={model.id}
      aria-labelledby={headingId}
      className="scroll-mt-32 rounded-md border border-line-soft bg-white"
    >
      <header className="flex flex-wrap items-baseline justify-between gap-3 border-b border-dashed border-line-soft px-6 py-5">
        <h2 id={headingId} className="font-display text-heading-compact text-ink">
          {model.name}
        </h2>
        <p className="font-mono text-label tracking-[0.15em] text-blue-deep uppercase">
          {formatBeadsPerResidue(model.beads_per_residue)}
        </p>
      </header>

      <div className="flex flex-col gap-8 px-6 py-6">
        <ModelDescription model={model} />

        <div className="grid gap-8 lg:grid-cols-2">
          {model.image_url && (
            <div className="flex flex-col gap-3">
              <h3 className="eyebrow">Representation</h3>
              <ModelImage src={model.image_url} modelName={model.name} />
            </div>
          )}
          <div className="flex min-w-0 flex-col gap-3">
            <h3 className="eyebrow">Atom mapping</h3>
            <div className="overflow-x-auto">
              <AtomMappingTable mapping={model.mapping} />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
