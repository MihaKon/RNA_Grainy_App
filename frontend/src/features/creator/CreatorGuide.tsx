import type { ReactNode } from "react";

import { STRATEGY_LABELS } from "./atoms";

export function CreatorGuide() {
  return (
    <div className="flex flex-col gap-5 text-sm text-ink-2">
      <GuideSection title="1. Define beads">
        <p>
          Choose <Term>Add bead</Term> and a mapping strategy, then click atoms on the
          2D diagram or in the atom list. Choose a bead using Select bead or its colored
          label on the diagram. Open Bead settings separately to edit its properties.
          Close the panel or press Escape to return to the two views. All four bases
          stay visible;
          <Term> Scope</Term> controls the mapping.
          <Term> Whole nucleotide</Term> lets you combine backbone and shared base
          atoms.
        </p>
        <p>
          <Term>Bead ID</Term> identifies the bead when building the structure and
          defining connections. <Term>Bead name</Term> becomes the atom name shown in
          the coarse-grained structure, so it must be unique within a residue.
        </p>
        <p>
          <Term>Scope</Term> sets the residues the bead is built for, and the atoms it
          offers are the ones all of those residues have. To place a bead on different
          atoms depending on the residue, add several beads with the same ID, e.g.{" "}
          <Code>A3</Code> for purines and <Code>A3</Code> for pyrimidines, or one bead
          per base with the A, G, C and U scopes.
        </p>
        <p>
          Editable bases and available atoms are highlighted. Click an atom outside the
          current scope to choose a compatible scope and select it. Compatible existing
          atoms are retained when changing scope this way.
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
          Choose <Term>Connect beads → Intra-residue</Term> and click two colored bead
          labels to toggle their connection within a residue. Connections use bead IDs
          and apply to all bases.
        </p>
        <p>
          Choose <Term>Connect beads → Inter-residue</Term>, then click the source bead
          for residue i and the target bead for residue i+1. The connection appears
          below the diagrams. You can connect the same bead ID to itself across
          residues. Only one inter-residue connection is supported; drawing another
          replaces it.
        </p>
        <p>
          For example, SimRNA links <Code>A2</Code> in residue i to <Code>A1</Code> in
          residue i+1. A connection applies to every bead with that ID.
        </p>
      </GuideSection>

      <GuideSection title="Live preview">
        <p>
          Molstar uses experimental coordinates from the selected example. Preview all
          RNA residues or one nucleotide of a chosen base. Toggle the coarse-grained and
          all-atom layers independently. Edits preserve the camera; changing the example
          or residue selection reframes the view. Missing atoms are skipped, as in
          conversion. Modified nucleotides use their recorded parent base. Water,
          ligands and proteins are omitted from the 3D preview. Input atom counts follow
          Results and include all first-model polymer atoms.
        </p>
      </GuideSection>

      <GuideSection title="4. Use or export the model">
        <p>
          Open <Term>Model details</Term> to edit the model name and description. The
          adjacent <Term>Model actions</Term> menu contains templates, JSON import and
          JSON export. <Term>User guide</Term> opens these instructions.
        </p>
        <p>
          <Term>Use model</Term> applies the model to this conversion once every issue
          is resolved. <Term>Export model as JSON</Term> saves the definition so you can
          load it again with <Term>Import model from JSON</Term> or as a custom model
          file. Start a new model with <Term>Start from scratch</Term> or{" "}
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
