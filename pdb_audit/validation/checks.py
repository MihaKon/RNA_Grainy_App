from typing import cast

from gemmi import (
    ConnectionType,
    EntityType,
    PolymerType,
    cif,
    find_tabulated_residue,
    make_address,
)

from app.services.structures import StructureProcessor
from pdb_audit.issues import IssueContent, Issues
from pdb_audit.validation.context import ValidationContext
from pdb_audit.validation.helpers import (
    CANONICAL_DNA_RESIDUES,
    ResidueKey,
    get_bead_atom_names_for_residue,
    get_connection_key,
    get_original_atom_counts_by_entity_type,
    get_parsed_atom_counts_by_entity_type,
    get_residue_entity_category,
    get_residue_key,
    get_structure_atom_count,
    is_bead_constructible,
    iter_chains,
    iter_residues,
    make_issue,
)

# GENERAL ISSUES #


def check_invalid_number_of_aa_atoms(context: ValidationContext) -> list[IssueContent]:
    original_reference_cif = cif.read_string(
        context.original_reference_cif
    ).sole_block()

    original_atom_count = len(original_reference_cif.find_values("_atom_site.id"))
    parsed_atom_count = get_structure_atom_count(context.reference_structure)
    if original_atom_count == parsed_atom_count:
        return []

    return [
        make_issue(
            Issues.INVALID_NUMBER_OF_AA_ATOMS,
            details=f"raw={original_atom_count}, parsed={parsed_atom_count}, difference={parsed_atom_count - original_atom_count}.",
        )
    ]


def check_invalid_number_of_aa_atoms_by_entity_type(
    context: ValidationContext,
) -> list[IssueContent]:
    original_counts = get_original_atom_counts_by_entity_type(
        context.original_reference_cif
    )
    parsed_counts = get_parsed_atom_counts_by_entity_type(context.reference_structure)

    categories = set(original_counts) | set(parsed_counts)

    differences = {}

    for category in categories:
        if original_counts[category] != parsed_counts[category]:
            differences[category] = {
                "original": original_counts[category],
                "parsed": parsed_counts[category],
            }

    if not differences:
        return []

    return [
        make_issue(
            issue=Issues.INVALID_NUMBER_OF_AA_ATOMS_BY_ENTITY_TYPE,
            details=f"Differences by entity type: \n {differences}",
        )
    ]


def check_empty_models(context: ValidationContext) -> list[IssueContent]:
    if len(context.coarse_grain_structure) == 0:
        return [make_issue(Issues.EMPTY_MODEL)]

    issues = []

    for model in context.coarse_grain_structure:
        if model.count_atom_sites() == 0:
            issues.append(
                make_issue(
                    issue=Issues.EMPTY_MODEL,
                    model=model,
                )
            )

    return issues


def check_empty_chains(context: ValidationContext) -> list[IssueContent]:
    issues = []

    for model, chain in iter_chains(context.coarse_grain_structure):
        if len(chain) == 0:
            issues.append(
                make_issue(
                    issue=Issues.EMPTY_CHAIN,
                    model=model,
                    chain=chain,
                )
            )

    return issues


# METADATA ISSUES #


def check_reference_cif_entity_metadata_lost(
    context: ValidationContext,
) -> list[IssueContent]:
    original_block = cif.read_string(context.original_reference_cif).sole_block()
    serialized_cif = StructureProcessor.reference_structure_to_cif_string(
        structure=context.reference_structure,
        source_content=context.original_reference_cif,
        filename=context.file_name,
    )
    serialized_block = cif.read_string(serialized_cif).sole_block()

    required_tags = (
        "_entity.id",
        "_entity.type",
        "_entity.pdbx_description",
        "_entity_poly.entity_id",
        "_entity_poly.type",
        "_struct_asym.id",
        "_struct_asym.entity_id",
        "_atom_site.label_entity_id",
        "_chem_comp.id",
        "_chem_comp.type",
        "_pdbx_struct_mod_residue.label_comp_id",
        "_pdbx_struct_mod_residue.parent_comp_id",
    )

    missing_tags = []

    for tag in required_tags:
        if original_block.find_values(tag) and not serialized_block.find_values(tag):
            missing_tags.append(tag)

    if not missing_tags:
        return []

    return [
        make_issue(
            Issues.REFERENCE_CIF_ENTITY_METADATA_LOST,
            details=f"Missing mmCIF tags after serialization: {', '.join(missing_tags)}",
        )
    ]


# MISSING, WRONG OR INCOMPLETE RESIDUES IN THE STRUCTURE #


def check_missing_modified_residue(
    context: ValidationContext,
) -> list[IssueContent]:
    reference = context.reference_structure
    model_config = context.coarse_grain_model.nucleotides_config

    modified_rna = {
        (mod.chain_name, str(mod.res_id.seqid), mod.res_id.name): mod.parent_comp_id
        for mod in reference.mod_residues
        if mod.parent_comp_id in {"A", "C", "G", "U"}
    }

    coarse_residues = {
        get_residue_key(model, chain, residue)
        for model, chain, residue in iter_residues(context.coarse_grain_structure)
        if len(residue) > 0
    }

    missing_count = 0
    examples: list[str] = []

    for model, chain, residue in iter_residues(reference):
        parent = modified_rna.get((chain.name, str(residue.seqid), residue.name))
        if parent is None:
            continue

        if residue.entity_type == EntityType.NonPolymer:
            continue

        if residue.name in model_config:
            continue

        if get_residue_key(model, chain, residue) in coarse_residues:
            continue

        missing_count += 1
        if len(examples) < 5:
            examples.append(
                f"model={model.num}, chain={chain.name}, "
                f"residue={residue.seqid} {residue.name} "
                f"(parent={parent})"
            )

    if missing_count == 0:
        return []

    return [
        make_issue(
            issue=Issues.MISSING_MODIFIED_RESIDUE,
            details=(
                f"Modified RNA residues not represented in CG: {missing_count}. "
                f"First {len(examples)}: {'; '.join(examples)}"
            ),
        )
    ]


def check_bead_skipped_due_to_missing_source_atoms(
    context: ValidationContext,
) -> list[IssueContent]:
    issues = []
    model_config = context.coarse_grain_model.nucleotides_config

    coarse_beads: set[tuple[ResidueKey, str]] = set()
    for model, chain, residue in iter_residues(context.coarse_grain_structure):
        for atom in residue:
            coarse_beads.add((get_residue_key(model, chain, residue), atom.name))

    for model, chain, residue in iter_residues(context.reference_structure):
        if (
            residue.name not in model_config
            or residue.entity_type == EntityType.NonPolymer
        ):
            continue

        residue_key = get_residue_key(model, chain, residue)

        skipped_beads: list[str] = []
        for bead_id, bead_name in model_config[residue.name]["bead_names"].items():
            bead_atom_names = get_bead_atom_names_for_residue(
                coarse_grain_model=context.coarse_grain_model,
                residue_name=residue.name,
                bead_id=bead_id,
            )

            if not bead_atom_names:
                continue

            if is_bead_constructible(
                coarse_grain_model=context.coarse_grain_model,
                residue=residue,
                bead_id=bead_id,
            ):
                continue

            if (residue_key, bead_name) in coarse_beads:
                continue

            skipped_beads.append(
                f"{bead_name}: required one of [{', '.join(bead_atom_names)}], "
                f"missing [{', '.join(bead_atom_names)}]"
            )

        if not skipped_beads:
            continue

        issues.append(
            make_issue(
                issue=Issues.BEAD_SKIPPED_DUE_TO_MISSING_SOURCE_ATOMS,
                model=model,
                chain=chain,
                residue=residue,
                details=f"Skipped beads: {'; '.join(skipped_beads)}",
            )
        )

    return issues


def check_bead_missing_despite_available_source_atoms(
    context: ValidationContext,
) -> list[IssueContent]:
    issues = []
    model_config = context.coarse_grain_model.nucleotides_config

    coarse_beads: set[tuple[ResidueKey, str]] = set()
    for model, chain, residue in iter_residues(context.coarse_grain_structure):
        residue_key = get_residue_key(model, chain, residue)
        for atom in residue:
            coarse_beads.add((residue_key, atom.name))

    for model, chain, residue in iter_residues(context.reference_structure):
        if residue.name not in model_config:
            continue
        if residue.entity_type == EntityType.NonPolymer:
            continue

        residue_key = get_residue_key(model, chain, residue)
        missing_beads = []

        for bead_id, bead_name in model_config[residue.name]["bead_names"].items():
            if not is_bead_constructible(
                coarse_grain_model=context.coarse_grain_model,
                residue=residue,
                bead_id=bead_id,
            ):
                continue

            if (residue_key, bead_name) not in coarse_beads:
                missing_beads.append(bead_name)

        if missing_beads:
            issues.append(
                make_issue(
                    issue=Issues.BEAD_MISSING_DESPITE_AVAILABLE_SOURCE_ATOMS,
                    model=model,
                    chain=chain,
                    residue=residue,
                    details=f"Missing beads: {', '.join(missing_beads)}",
                )
            )

    return issues


def check_water_in_coarse_structure(context: ValidationContext) -> list[IssueContent]:
    issues = []

    for model, chain, residue in iter_residues(context.coarse_grain_structure):
        if get_residue_entity_category(residue) != "water":
            continue

        issues.append(
            make_issue(
                issue=Issues.WATER_IN_COARSE_STRUCTURE,
                model=model,
                chain=chain,
                residue=residue,
            )
        )

    return issues


def check_ligands_and_ions_in_coarse_structure(
    context: ValidationContext,
) -> list[IssueContent]:
    issues = []
    supported_residues = context.coarse_grain_model.nucleotides_config

    for model, chain, residue in iter_residues(context.coarse_grain_structure):
        category = get_residue_entity_category(residue)

        if category != "non-polymer":
            continue

        if residue.name in supported_residues:
            continue

        issues.append(
            make_issue(
                issue=Issues.LIGAND_OR_ION_IN_COARSE_STRUCTURE,
                model=model,
                chain=chain,
                residue=residue,
            )
        )

    return issues


def check_nucleotides_are_marked_as_polymer(
    context: ValidationContext,
) -> list[IssueContent]:
    issues = []

    supported_residues = context.coarse_grain_model.nucleotides_config

    for model, chain, residue in iter_residues(context.coarse_grain_structure):
        if (
            residue.name in supported_residues
            and residue.entity_type != EntityType.Polymer
        ):
            issues.append(
                make_issue(
                    issue=Issues.NUCLEOTIDE_NOT_MARKED_AS_POLYMER,
                    model=model,
                    chain=chain,
                    residue=residue,
                    details=(f"Entity type: {residue.entity_type.name}"),
                )
            )

    return issues


def check_protein_residues_in_coarse_structure(
    context: ValidationContext,
) -> list[IssueContent]:
    structure = context.coarse_grain_structure
    peptide_types = {
        PolymerType.PeptideL,
        PolymerType.PeptideD,
    }

    protein_count = 0
    examples: list[str] = []
    example_limit = 5

    for model, chain, residue in iter_residues(structure):
        if get_residue_entity_category(residue) != "polymer":
            continue
        entity = structure.get_entity(residue.entity_id) if residue.entity_id else None

        entity_is_protein = entity is not None and entity.polymer_type in peptide_types

        residue_is_amino_acid = find_tabulated_residue(residue.name).is_amino_acid()

        if not (entity_is_protein or residue_is_amino_acid):
            continue

        protein_count += 1

        if len(examples) < example_limit:
            examples.append(
                f"model={model.num}, "
                f"chain={chain.name}, "
                f"residue={residue.seqid}, "
                f"res_name={residue.name}"
            )

    if protein_count == 0:
        return []

    return [
        make_issue(
            issue=Issues.PROTEIN_RESIDUE_IN_COARSE_STRUCTURE,
            details=(
                f"Protein residues: {protein_count}. "
                f"First {len(examples)} examples: {'; '.join(examples)}"
            ),
        )
    ]


def check_dna_residues_in_coarse_structure(
    context: ValidationContext,
) -> list[IssueContent]:
    dna_residue_count = 0
    examples: list[str] = []
    example_limit = 5

    for model, chain, residue in iter_residues(context.coarse_grain_structure):
        if residue.name.upper() not in CANONICAL_DNA_RESIDUES:
            continue

        dna_residue_count += 1

        if len(examples) < example_limit:
            examples.append(
                f"model={model.num}, "
                f"chain={chain.name}, "
                f"residue={residue.seqid}, "
                f"res_name={residue.name}"
            )

    if dna_residue_count == 0:
        return []

    return [
        make_issue(
            Issues.DNA_RESIDUE_IN_COARSE_STRUCTURE,
            details=(
                f"Canonical DNA residues: {dna_residue_count}. "
                f"First {len(examples)} examples: "
                f"{'; '.join(examples)}"
            ),
        )
    ]


# CONNECTION ISSUES #


def check_connectivity_not_found(
    context: ValidationContext,
) -> list[IssueContent]:
    structure = context.coarse_grain_structure

    if len(structure) != 1:
        return []

    cg_model = context.coarse_grain_model
    model_config = cg_model.nucleotides_config
    raw_intra_rules, inter_rule = cg_model.connectivity_rules
    intra_rules = cast(
        list[list[str]] | dict[str, list[list[str]]],
        raw_intra_rules,
    )

    missing_count = 0
    examples: list[str] = []

    original_label_seq = {
        get_residue_key(model, chain, residue): residue.label_seq
        for model, chain, residue in iter_residues(context.reference_structure)
    }

    for chain in structure[0]:
        previous_residue = None

        for residue in chain:
            if residue.name not in model_config:
                previous_residue = None
                continue

            bead_names = model_config[residue.name]["bead_names"]

            if isinstance(intra_rules, dict):
                rules = intra_rules[
                    "purine" if residue.name in ("A", "G") else "pyrimidine"
                ]
            else:
                rules = intra_rules

            for source_id, target_id in rules:
                source_name = bead_names[source_id]
                target_name = bead_names[target_id]
                source = next((a for a in residue if a.name == source_name), None)
                target = next((a for a in residue if a.name == target_name), None)

                if source is None or target is None:
                    continue

                if (
                    structure.find_connection(
                        make_address(chain, residue, source),
                        make_address(chain, residue, target),
                    )
                    is None
                ):
                    missing_count += 1
                    if len(examples) < 5:
                        examples.append(
                            f"{chain.name}/{residue.seqid}: {source_name}-{target_name}"
                        )

            current_label_seq = original_label_seq.get(
                get_residue_key(structure[0], chain, residue)
            )

            previous_label_seq: int | None = (
                original_label_seq.get(
                    get_residue_key(structure[0], chain, previous_residue)
                )
                if previous_residue is not None
                else None
            )

            if (
                previous_residue is not None
                and inter_rule.get("tail")
                and inter_rule.get("head")
                and previous_label_seq
                and current_label_seq
                and current_label_seq == previous_label_seq + 1
            ):
                previous_bead_names = model_config[previous_residue.name]["bead_names"]
                tail_name = previous_bead_names[inter_rule["tail"]]
                head_name = bead_names[inter_rule["head"]]

                tail = next((a for a in previous_residue if a.name == tail_name), None)
                head = next((a for a in residue if a.name == head_name), None)

                if tail is not None and head is not None:
                    if (
                        structure.find_connection(
                            make_address(chain, previous_residue, tail),
                            make_address(chain, residue, head),
                        )
                        is None
                    ):
                        missing_count += 1
                        if len(examples) < 5:
                            examples.append(
                                f"{chain.name}/{previous_residue.seqid}"
                                f"-{residue.seqid}: {tail_name}-{head_name}"
                            )

            previous_residue = residue

    if missing_count == 0:
        return []

    return [
        make_issue(
            issue=Issues.CONNECTIVITY_NOT_FOUND,
            details=(
                f"Expected connections missing: {missing_count}. "
                f"First {len(examples)}: {'; '.join(examples)}"
            ),
        )
    ]


def check_connectivity_between_invalid_beads(
    context: ValidationContext,
) -> list[IssueContent]:
    structure = context.coarse_grain_structure
    if len(structure) != 1:
        return []

    model = structure[0]
    model_config = context.coarse_grain_model.nucleotides_config
    raw_intra_rules, inter_rule = context.coarse_grain_model.connectivity_rules
    intra_rules = cast(
        list[list[str]] | dict[str, list[list[str]]],
        raw_intra_rules,
    )

    allowed: set[frozenset[tuple[str, ...]]] = set()
    original_label_seq = {
        get_residue_key(ref_model, ref_chain, ref_residue): ref_residue.label_seq
        for ref_model, ref_chain, ref_residue in iter_residues(
            context.reference_structure
        )
    }

    for chain in model:
        previous_residue = None

        for residue in chain:
            if residue.name not in model_config:
                previous_residue = None
                continue

            bead_names = model_config[residue.name]["bead_names"]
            atoms = {atom.name: atom for atom in residue}

            current_label_seq = original_label_seq.get(
                get_residue_key(model, chain, residue)
            )
            previous_label_seq: int | None = (
                original_label_seq.get(get_residue_key(model, chain, previous_residue))
                if previous_residue is not None
                else None
            )

            if isinstance(intra_rules, dict):
                rules = intra_rules[
                    "purine" if residue.name in ("A", "G") else "pyrimidine"
                ]
            else:
                rules = intra_rules

            for source_id, target_id in rules:
                source = atoms.get(bead_names[source_id])
                target = atoms.get(bead_names[target_id])

                if source is not None and target is not None:
                    allowed.add(
                        get_connection_key(
                            make_address(chain, residue, source),
                            make_address(chain, residue, target),
                        )
                    )

            if (
                previous_residue is not None
                and inter_rule.get("tail")
                and inter_rule.get("head")
                and previous_label_seq
                and current_label_seq
                and current_label_seq == previous_label_seq + 1
            ):
                previous_bead_names = model_config[previous_residue.name]["bead_names"]
                previous_atoms = {atom.name: atom for atom in previous_residue}

                tail = previous_atoms.get(previous_bead_names[inter_rule["tail"]])
                head = atoms.get(bead_names[inter_rule["head"]])

                if tail is not None and head is not None:
                    allowed.add(
                        get_connection_key(
                            make_address(chain, previous_residue, tail),
                            make_address(chain, residue, head),
                        )
                    )

            previous_residue = residue

    invalid_count = 0
    examples: list[str] = []

    for connection in structure.connections:
        if (
            model.find_cra(connection.partner1).atom is None
            or model.find_cra(connection.partner2).atom is None
        ):
            continue

        if get_connection_key(connection.partner1, connection.partner2) in allowed:
            continue

        invalid_count += 1
        if len(examples) < 5:
            examples.append(
                f"{connection.name}: {connection.partner1} -> {connection.partner2}"
            )

    if invalid_count == 0:
        return []

    return [
        make_issue(
            issue=Issues.CONNECTIVITY_BETWEEN_INVALID_BEADS,
            details=(
                f"Connections not allowed by model rules: {invalid_count}. "
                f"First {len(examples)}: {'; '.join(examples)}"
            ),
        )
    ]


def check_duplicated_connectivity(
    context: ValidationContext,
) -> list[IssueContent]:
    structure = context.coarse_grain_structure

    if len(structure) != 1:
        return []

    seen = set()
    duplicate_count = 0
    examples: list[str] = []

    for connection in structure.connections:
        endpoints = tuple(
            sorted(
                (
                    address.chain_name,
                    address.res_id.name,
                    str(address.res_id.seqid),
                    address.res_id.segment,
                    address.atom_name,
                    address.altloc,
                )
                for address in (connection.partner1, connection.partner2)
            )
        )

        if endpoints in seen:
            duplicate_count += 1
            if len(examples) < 5:
                examples.append(
                    f"{connection.name}: {connection.partner1} ↔ {connection.partner2}"
                )
        else:
            seen.add(endpoints)

    if duplicate_count == 0:
        return []

    return [
        make_issue(
            issue=Issues.DUPLICATED_CONNECTIVITY,
            details=(
                f"Duplicate connections: {duplicate_count}. "
                f"First {len(examples)}: {'; '.join(examples)}"
            ),
        )
    ]


def check_connectivity_with_not_existent_bead(
    context: ValidationContext,
) -> list[IssueContent]:
    structure = context.coarse_grain_structure
    broken_count = 0
    examples: list[str] = []

    for connection in structure.connections:
        exists_in_one_model = any(
            model.find_cra(connection.partner1).atom is not None
            and model.find_cra(connection.partner2).atom is not None
            for model in structure
        )
        if exists_in_one_model:
            continue

        broken_count += 1
        if len(examples) < 5:
            examples.append(
                f"{connection.name}: {connection.partner1} → {connection.partner2}"
            )

    if broken_count == 0:
        return []

    return [
        make_issue(
            issue=Issues.CONNECTIVITY_WITH_NOT_EXISTENT_BEAD,
            details=(
                f"Connections without both beads in one model: {broken_count}. "
                f"First {len(examples)}: {'; '.join(examples)}"
            ),
        )
    ]


def check_wrong_connectivity_type(
    context: ValidationContext,
) -> list[IssueContent]:
    wrong = [
        connection
        for connection in context.coarse_grain_structure.connections
        if connection.type != ConnectionType.Covale
    ]

    if not wrong:
        return []

    examples = "; ".join(
        f"{connection.name}: {connection.type.name}" for connection in wrong[:5]
    )
    return [
        make_issue(
            issue=Issues.WRONG_CONNECTIVITY_TYPE,
            details=f"Non-covalent connections: {len(wrong)}. First examples: {examples}",
        )
    ]


def check_excessive_connectivity_length(
    context: ValidationContext,
) -> list[IssueContent]:
    structure = context.coarse_grain_structure

    if len(structure) != 1:
        return []

    max_length = 8.0
    model = structure[0]
    long_count = 0
    examples: list[str] = []

    for connection in structure.connections:
        atom1 = model.find_cra(connection.partner1).atom
        atom2 = model.find_cra(connection.partner2).atom

        if atom1 is None or atom2 is None:
            continue

        distance = atom1.pos.dist(atom2.pos)
        if distance <= max_length:
            continue

        long_count += 1
        examples.append(
            f"{connection.name}: "
            f"{connection.partner1} -> {connection.partner2} "
            f"({distance:.2f} Å)"
        )

    if long_count == 0:
        return []

    return [
        make_issue(
            issue=Issues.EXCESSIVE_CONNECTIVITY_LENGTH,
            details=(
                f"Connections longer than {max_length:g} Å: {long_count}. "
                f"{len(examples)} examples: {'; '.join(examples)}"
            ),
        )
    ]


# ALT LOCS ISSUES #


def check_alt_loc_present(context: ValidationContext) -> list[IssueContent]:
    count = 0
    examples: list[str] = []
    example_limit = 5

    for model, chain, residue in iter_residues(context.reference_structure):
        altlocs = {atom.altloc for atom in residue if atom.altloc not in ("\0", " ")}

        if not altlocs:
            continue

        count += 1

        if len(examples) < example_limit:
            examples.append(
                f"model={model.num}, "
                f"chain={chain.name}, "
                f"residue={residue.seqid}, "
                f"res_name={residue.name}, "
                f"altlocs={sorted(altlocs)}"
            )

    if count == 0:
        return []

    return [
        make_issue(
            issue=Issues.ALT_LOC_PRESENT,
            details=(
                f"Residues with alternative locations: {count}. "
                f"First {len(examples)} examples: {'; '.join(examples)}"
            ),
        )
    ]
