from gemmi import EntityType, PolymerType, cif, find_tabulated_residue

from app.services.structures import StructureProcessor
from pdb_audit.issues import IssueContent, Issues
from pdb_audit.validation.context import ValidationContext
from pdb_audit.validation.helpers import (
    get_original_atom_counts_by_entity_type,
    get_parsed_atom_counts_by_entity_type,
    get_residue_entity_category,
    get_structure_atom_count,
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
        residue_count = sum(len(chain) for chain in model)
        if residue_count == 0:
            issues.append(make_issue(Issues.EMPTY_MODEL, model=model))
    return issues


# METADATA ISSUES #


def check_reference_cif_entity_metadata_lost(
    context: ValidationContext,
) -> list[IssueContent]:
    original_block = cif.read_string(context.original_reference_cif).sole_block()

    serialized_cif = StructureProcessor.reference_structure_to_cif_string(
        context.reference_structure, context.original_reference_cif
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


# MISSING, WRONG OR INCOMPLETE RESIDUES #


def check_water_in_coarse_structure(
    context: ValidationContext,
) -> list[IssueContent]:
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

        if entity is not None and entity.polymer_type != PolymerType.Unknown:
            is_protein = entity.polymer_type in peptide_types
        else:
            is_protein = find_tabulated_residue(residue.name).is_amino_acid()

        if not is_protein:
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
