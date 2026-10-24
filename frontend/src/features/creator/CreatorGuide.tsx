import type { ReactNode } from "react";

import { STRATEGY_LABELS } from "./atoms";

export function CreatorGuide() {
  return (
    <div className="flex flex-col gap-5 text-sm text-ink-2">
      <GuideSection title="1. Define beads">
        <p>
          <Term>Bead ID</Term> identifies the bead when building the structure and
          defining connections. <Term>Bead name</Term> becomes the atom name shown in
          the coarse-grained structure, so it must be unique within a residue.
        </p>
        <p>
          <Term>Applies to</Term> sets the residues the bead is built for, and the atoms
          it offers are the ones all of those residues have. To place a bead on
          different atoms depending on the residue, add several beads with the same ID,
          e.g. <Code>A3</Code> for purines and <Code>A3</Code> for pyrimidines, or one
          bead per base with the A, G, C and U scopes.
        </p>
      </GuideSection>

      <GuideSection title="2. Choose a mapping strategy">
        <ul className="flex list-disc flex-col gap-1 pl-5">
          <li>
            <Term>{STRATEGY_LABELS.direct}</Term> places the bead on one selected atom.
          </li>
          <li>
            <Term>{STRATEGY_LABELS.center_of_mass}</Term> places it at the mass-weighted
            center of the selected atoms.
          </li>
          <li>
            <Term>{STRATEGY_LABELS.geometric_center}</Term> places it at the average
            position of the selected atoms.
          </li>
        </ul>
      </GuideSection>

      <GuideSection title="3. Configure connectivity">
        <p>
          On the Connectivity tab, select the pairs of beads bonded within a residue,
          and one inter-residue connection from a bead of residue i to a bead of residue
          i+1, e.g. <Code>A2</Code> → <Code>A1</Code> in SimRNA. A connection applies to
          every bead with that ID.
        </p>
      </GuideSection>

      <GuideSection title="4. Use or export the model">
        <p>
          <Term>Use model</Term> applies the model to this conversion once every issue
          is resolved. <Term>Export JSON</Term> saves the definition so you can load it
          again with <Term>Import JSON</Term> or as a custom model file. Start a new
          model with <Term>Start from scratch</Term> or{" "}
          <Term>Load SimRNA template</Term>.
        </p>
      </GuideSection>
    </div>
  );
}

function GuideSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2">
      <h4 className="font-medium text-ink">{title}</h4>
      {children}
    </section>
  );
}

function Term({ children }: { children: ReactNode }) {
  return <strong className="font-medium text-ink">{children}</strong>;
}

function Code({ children }: { children: ReactNode }) {
  return <code className="font-mono">{children}</code>;
}
