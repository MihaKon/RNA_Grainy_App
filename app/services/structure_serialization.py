import re

from gemmi import MmcifOutputGroups, PdbWriteOptions, Structure, cif

from app.models.form import SupportedFormats

REFERENCE_MMCIF_CATEGORIES = (
    "_entity.",
    "_chem_comp.",
    "_pdbx_struct_mod_residue.",
)


def base_mmcif_groups() -> MmcifOutputGroups:
    """Select mmCIF categories shared by reference and CG output."""

    groups = MmcifOutputGroups(False)
    groups.atoms = True
    groups.group_pdb = True
    groups.entry = True
    groups.title_keywords = True
    groups.cell = True
    groups.conn = True
    groups.entity = True
    groups.entity_poly = True
    groups.struct_asym = True
    return groups


def base_pdb_options(minimal: bool) -> PdbWriteOptions:
    """Configure PDB output to preserve atom serials and write CONECT records."""

    options = PdbWriteOptions(minimal=minimal)
    options.preserve_serial = True
    options.conect_records = True
    options.link_records = False
    return options


def set_mmcif_entry_id(
    block: cif.Block,
    structure: Structure,
    filename: str | None,
    is_coarse: bool,
    model_name: str | None = None,
) -> None:
    """Set a readable mmCIF identifier, appending the model name for CG output.
    Prefer an existing entry ID, then the uploaded filename, structure name,
    and CIF block name. Preserve an existing reference entry ID.
    """

    raw_id = block.find_value("_entry.id")
    entry_id = cif.as_string(raw_id).strip() if raw_id is not None else ""

    candidates = (entry_id, filename or "", structure.name, block.name)
    base_name = next(
        (
            value.strip()
            for value in candidates
            if value and value.strip() not in ("", "?", ".")
        ),
        "coarse_grained",
    )
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", base_name).strip("_")
    safe_name = safe_name or "coarse_grained"

    if is_coarse:
        safe_model_name = (
            re.sub(r"[^A-Za-z0-9_-]+", "_", model_name or "coarse_grained").strip("_")
            or "coarse_grained"
        )

        coarse_id = f"{safe_name}_{safe_model_name}"
        block.name = coarse_id
        block.set_pair("_entry.id", coarse_id)
    elif entry_id in ("", "?", "."):
        block.set_pair("_entry.id", safe_name)
        block.name = safe_name


def add_pdb_header_and_title(
    pdb_structure: Structure,
    pdb_content: str,
    filename: str | None,
    model_name: str | None,
    source_content: str | None,
    source_format: SupportedFormats | None,
) -> str:
    """Prepend source HEADER when available and name the CG structure in TITLE.
    For PDB input, reuse its HEADER. For mmCIF input, ask Gemmi to generate
    a PDB HEADER from the available structure metadata.
    """

    prefix: list[str] = []
    header = None

    if source_format == SupportedFormats.PDB and source_content is not None:
        header = next(
            (line for line in source_content.splitlines() if line.startswith("HEADER")),
            None,
        )
    elif source_format in (SupportedFormats.CIF, SupportedFormats.MMCIF):
        generated_headers = pdb_structure.make_pdb_string(
            options=PdbWriteOptions(headers_only=True)
        )
        header = next(
            (
                line
                for line in generated_headers.splitlines()
                if line.startswith("HEADER")
            ),
            None,
        )

    if header is not None:
        prefix.append(header)

    if model_name is not None:
        entry_id = (
            pdb_structure.info["_entry.id"].strip()
            if "_entry.id" in pdb_structure.info
            else ""
        )
        base_name = (
            entry_id if entry_id not in ("", "?", ".") else filename or "coarse_grained"
        )
        prefix.append(f"TITLE     {base_name}_{model_name}")

    return "\n".join(prefix) + "\n" + pdb_content if prefix else pdb_content


def reference_structure_to_pdb_string(
    structure: Structure,
) -> str:
    """Serialize a cloned reference structure as PDB with its metadata."""

    pdb_structure = structure.clone()
    options = base_pdb_options(minimal=False)

    pdb_structure.shorten_chain_names()
    return pdb_structure.make_pdb_string(options=options)


def coarse_structure_to_pdb_string(
    structure: Structure,
    filename: str | None,
    model_name: str,
    source_content: str,
    source_format: SupportedFormats,
) -> str:
    """Serialize CG as PDB with minimal metadata and generated connectivity."""

    pdb_structure = structure.clone()
    options = base_pdb_options(minimal=True)
    options.cryst1_record = False
    options.end_record = True

    pdb_structure.shorten_chain_names()
    pdb_content = pdb_structure.make_pdb_string(options=options)

    return add_pdb_header_and_title(
        pdb_structure=pdb_structure,
        pdb_content=pdb_content,
        filename=filename,
        model_name=model_name,
        source_content=source_content,
        source_format=source_format,
    )


def coarse_structure_to_cif_string(
    structure: Structure,
    model_name: str,
    filename: str | None = None,
) -> str:
    """Serialize CG atoms, connectivity and polymer metadata as mmCIF."""

    groups = base_mmcif_groups()
    groups.title_keywords = False
    groups.cell = False
    groups.entity_poly_seq = True

    document = structure.make_mmcif_document(groups=groups)
    set_mmcif_entry_id(
        document.sole_block(),
        structure,
        filename,
        is_coarse=True,
        model_name=model_name,
    )
    return document.as_string()


def reference_structure_to_cif_string(
    structure: Structure,
    source_content: str,
    filename: str,
) -> str:
    """Serialize the reference and restore selected metadata from source mmCIF.

    Gemmi does not reproduce every source category during serialization, so
    entity, chemical-component and modified-residue categories are copied
    from the input document.
    """

    groups = base_mmcif_groups()
    groups.entity_poly_seq = True
    groups.chem_comp = True

    document = structure.make_mmcif_document(groups=groups)
    target_block = document.sole_block()
    source_block = cif.read_string(source_content).sole_block()

    for category in REFERENCE_MMCIF_CATEGORIES:
        source_data = source_block.get_mmcif_category(category, raw=True)
        if source_data:
            target_block.set_mmcif_category(
                category,
                source_data,
                raw=True,
            )

    set_mmcif_entry_id(
        target_block,
        structure,
        filename,
        is_coarse=False,
    )
    return document.as_string()
