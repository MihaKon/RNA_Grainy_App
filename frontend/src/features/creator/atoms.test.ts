import { describe, expect, it } from "vitest";

import { BEAD_SCOPES, residuesForScope, SCOPES } from "./atoms";

const RESIDUE_ATOMS: Record<string, readonly string[]> = {
  A: SCOPES.adenine.atoms,
  C: SCOPES.cytosine.atoms,
  G: SCOPES.guanine.atoms,
  U: SCOPES.uracil.atoms,
};

describe("SCOPES", () => {
  it("offers only atoms that every residue of a base scope has", () => {
    const baseScopes = BEAD_SCOPES.filter(
      (scope) => scope !== "phosphate" && scope !== "sugar",
    );

    for (const scope of baseScopes) {
      for (const residue of residuesForScope(scope)) {
        expect(RESIDUE_ATOMS[residue], `${scope} in ${residue}`).toEqual(
          expect.arrayContaining([...SCOPES[scope].atoms]),
        );
      }
    }
  });

  it("offers the ring atoms shared by all bases", () => {
    expect(SCOPES.all.atoms).toEqual(["N1", "C2", "N3", "C4", "C5", "C6"]);
  });
});
