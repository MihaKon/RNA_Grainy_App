import { CIF } from "molstar/lib/mol-io/reader/cif";

import { ALL_RESIDUES, type Residue, residuesForScope } from "./atoms";
import type { ModelDraft } from "./modelDraft";
import { atomicMass } from "./nucleotideDiagram";

export interface PreviewAtom {
  name: string;
  element: string;
  x: number;
  y: number;
  z: number;
}

export interface PreviewResidue {
  name?: string;
  inputAtomCount?: number;
  base: Residue;
  chain: string;
  sequence: number;
  atoms: PreviewAtom[];
}

export async function readPreviewSource(text: string) {
  const parsed = await CIF.parseText(text).run();
  if (parsed.isError) throw new Error("Could not read the example structure.");
  const categories = parsed.result.blocks[0]?.categories;
  const site = categories?.atom_site;
  if (!site) throw new Error("The example has no atom coordinates.");
  const value = (name: string, row: number) => site.getField(name)?.str(row) ?? "";
  const entities = categories.entity;
  const polymerIds = new Set<string>();
  for (let row = 0; row < (entities?.rowCount ?? 0); row++) {
    if (entities?.getField("type")?.str(row) === "polymer")
      polymerIds.add(entities.getField("id")?.str(row) ?? "");
  }
  const modifications = categories.pdbx_struct_mod_residue;
  const parents = new Map<string, string>();
  for (let row = 0; row < (modifications?.rowCount ?? 0); row++) {
    const field = (name: string) => modifications?.getField(name)?.str(row) ?? "";
    parents.set(
      `${field("label_asym_id")}:${field("label_seq_id")}:${field("label_comp_id")}`,
      field("parent_comp_id"),
    );
  }
  let originalAtomCount = 0;
  const residues = new Map<string, PreviewResidue>();
  const firstModel = value("pdbx_PDB_model_num", 0);
  for (let row = 0; row < site.rowCount; row++) {
    if (value("pdbx_PDB_model_num", row) !== firstModel) continue;
    const polymer = polymerIds.has(value("label_entity_id", row));
    if (polymer) originalAtomCount++;
    const chain = value("label_asym_id", row);
    const sequence = Number(value("label_seq_id", row));
    const name = value("label_comp_id", row);
    const parent = parents.get(`${chain}:${sequence.toString()}:${name}`) ?? name;
    const base = ALL_RESIDUES.find((base) => base === parent);
    if (!base || !polymer) continue;
    const key = `${chain}:${sequence.toString()}`;
    const residue = residues.get(key) ?? {
      base,
      name,
      chain,
      sequence,
      atoms: [],
      inputAtomCount: 0,
    };
    residue.inputAtomCount = (residue.inputAtomCount ?? 0) + 1;
    residues.set(key, residue);
    const alt = value("label_alt_id", row);
    if (alt && alt !== "." && alt !== "?" && alt !== "A") continue;
    const atomName = value("label_atom_id", row);
    if (!residue.atoms.some((atom) => atom.name === atomName)) {
      residue.atoms.push({
        name: atomName,
        element: value("type_symbol", row),
        x: Number(value("Cartn_x", row)),
        y: Number(value("Cartn_y", row)),
        z: Number(value("Cartn_z", row)),
      });
    }
  }
  if (residues.size === 0) throw new Error("The example has no standard RNA residues.");
  return { residues: [...residues.values()], originalAtomCount };
}

function cifValue(value: string | number): string {
  const text = String(value);
  if (text === "." || text === "?") return text;
  if (
    !/[\s'"#;]/.test(text) &&
    text &&
    !/^(?:[_$]|data_|save_|loop_|stop_|global_)/i.test(text)
  )
    return text;
  if (!text.includes('"')) return `"${text}"`;
  if (!text.includes("'")) return `'${text}'`;
  return `\n;${text}\n;\n`;
}

function loop(category: string, fields: string[], rows: (string | number)[][]): string {
  return `loop_\n${fields.map((field) => `_${category}.${field}`).join("\n")}\n${rows.map((row) => row.map(cifValue).join(" ")).join("\n")}\n#\n`;
}

export function buildPreview(
  draft: ModelDraft,
  source: PreviewResidue[],
  selection: "all" | Residue,
  totalInputAtoms?: number,
) {
  const residues =
    selection === "all"
      ? source
      : source.filter((residue) => residue.base === selection).slice(0, 1);
  const coarse: PreviewResidue[] = [];
  const beadNames = new Map<PreviewResidue, Map<string, string>>();
  for (const residue of residues) {
    const names = new Map<string, string>();
    const atoms: PreviewAtom[] = [];
    for (const bead of draft.beads) {
      if (!residuesForScope(bead.scope).includes(residue.base)) continue;
      const selected = bead.atoms.flatMap((name) =>
        residue.atoms.filter((atom) => atom.name === name),
      );
      const first = selected[0];
      if (!first) continue;
      if (bead.strategy === "direct" && first.name !== bead.atoms[0]) continue;
      const weights = selected.map((atom) =>
        bead.strategy === "center_of_mass" ? atomicMass(atom.element) : 1,
      );
      const total = weights.reduce((a, b) => a + b, 0);
      const coordinate = (axis: "x" | "y" | "z") =>
        selected.reduce((sum, atom, i) => sum + atom[axis] * (weights[i] ?? 1), 0) /
        total;
      atoms.push({
        name: bead.name,
        element: bead.strategy === "direct" ? first.element : "C",
        x: bead.strategy === "direct" ? first.x : coordinate("x"),
        y: bead.strategy === "direct" ? first.y : coordinate("y"),
        z: bead.strategy === "direct" ? first.z : coordinate("z"),
      });
      names.set(bead.beadId, bead.name);
    }
    const mapped = { ...residue, name: residue.base, atoms };
    coarse.push(mapped);
    beadNames.set(mapped, names);
  }
  const connections: (string | number)[][] = [];
  const connect = (a: PreviewResidue, aId: string, b: PreviewResidue, bId: string) => {
    const aName = beadNames.get(a)?.get(aId),
      bName = beadNames.get(b)?.get(bId);
    if (!aName || !bName) return;
    connections.push([
      `bond${(connections.length + 1).toString()}`,
      "covale",
      a.chain,
      a.base,
      a.sequence,
      aName,
      "1_555",
      b.chain,
      b.base,
      b.sequence,
      bName,
      "1_555",
    ]);
  };
  coarse.forEach((residue, i) => {
    draft.intraResidue.forEach(([a, b]) => {
      connect(residue, a, residue, b);
    });
    const next = coarse[i + 1];
    const { source, target } = draft.interResidue;
    if (
      next?.chain === residue.chain &&
      next.sequence === residue.sequence + 1 &&
      source &&
      target
    )
      connect(residue, source, next, target);
  });
  const serialize = (residues: PreviewResidue[], bonds: (string | number)[][] = []) => {
    let serial = 0;
    return (
      "data_preview\n#\n" +
      loop("entity", ["id", "type"], [[1, "polymer"]]) +
      loop("entity_poly", ["entity_id", "type"], [[1, "polyribonucleotide"]]) +
      loop(
        "struct_asym",
        ["id", "entity_id"],
        [...new Set(residues.map((residue) => residue.chain))].map((chain) => [
          chain,
          1,
        ]),
      ) +
      loop(
        "atom_site",
        [
          "group_PDB",
          "id",
          "type_symbol",
          "label_atom_id",
          "label_alt_id",
          "label_comp_id",
          "label_asym_id",
          "label_entity_id",
          "label_seq_id",
          "Cartn_x",
          "Cartn_y",
          "Cartn_z",
          "occupancy",
          "B_iso_or_equiv",
          "auth_seq_id",
          "auth_comp_id",
          "auth_asym_id",
          "auth_atom_id",
          "pdbx_PDB_model_num",
        ],
        residues.flatMap((residue) =>
          residue.atoms.map((atom) => [
            "ATOM",
            ++serial,
            atom.element,
            atom.name,
            ".",
            residue.name ?? residue.base,
            residue.chain,
            1,
            residue.sequence,
            atom.x.toFixed(4),
            atom.y.toFixed(4),
            atom.z.toFixed(4),
            1,
            0,
            residue.sequence,
            residue.name ?? residue.base,
            residue.chain,
            atom.name,
            1,
          ]),
        ),
      ) +
      (bonds.length
        ? loop(
            "struct_conn",
            [
              "id",
              "conn_type_id",
              "ptnr1_label_asym_id",
              "ptnr1_label_comp_id",
              "ptnr1_label_seq_id",
              "ptnr1_label_atom_id",
              "ptnr1_symmetry",
              "ptnr2_label_asym_id",
              "ptnr2_label_comp_id",
              "ptnr2_label_seq_id",
              "ptnr2_label_atom_id",
              "ptnr2_symmetry",
            ],
            bonds,
          )
        : "")
    );
  };
  const original =
    selection === "all" && totalInputAtoms !== undefined
      ? totalInputAtoms
      : residues.reduce(
          (sum, residue) => sum + (residue.inputAtomCount ?? residue.atoms.length),
          0,
        );
  const count = coarse.reduce((sum, residue) => sum + residue.atoms.length, 0);
  return {
    reference: serialize(residues),
    coarse: serialize(coarse, connections),
    count,
    atomCounts: {
      original,
      coarse: count,
      reduction: original ? 1 - count / original : 0,
    },
    residueCount: residues.length,
  };
}
