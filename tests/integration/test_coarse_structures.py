from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from gemmi import cif, make_structure_from_block, read_pdb_string

from tests.integration.helpers import AtomKey, extract_data_attribute, get_atoms


@pytest.mark.parametrize(
    "structure_id",
    ["4GXY", "1EHZ", "1RNA", "2MIY", "2F8S", "R1212TS063_4", "rnacomposer_example1"],
)
@pytest.mark.parametrize("input_format", ["pdb", "cif"])
@pytest.mark.parametrize(
    "selected_model",
    [
        "SimModel",
        "NASTModel",
        "YUPModel",
        "RNAJPModel",
        "FebModel",
        "VFoldModel",
        "Nares2PModel",
        "TopRNAModel",
        "IFoldRNAModel",
        "IsRNAOneModel",
        "IsRNATwoModel",
        "HireModel",
    ],
)
def test_coarse_pdb_and_cif_exports_are_consistent(
    client: TestClient,
    test_data_dir: Path,
    isolated_workspace_storage: Path,
    structure_id: str,
    input_format: str,
    selected_model: str,
) -> None:
    input_path = test_data_dir / f"{structure_id}.{input_format}"
    upload_response = client.post(
        "/upload/file/",
        data={
            "selected_model": selected_model,
            "models": "1",
        },
        files={
            "file": (
                input_path.name,
                input_path.read_bytes(),
                "application/octet-stream",
            ),
        },
    )

    assert upload_response.status_code == 200, upload_response.text

    download_urls = {
        "pdb": extract_data_attribute(
            upload_response.text,
            "data-coarse-pdb-url",
        ),
        "cif": extract_data_attribute(
            upload_response.text,
            "data-coarse-cif-url",
        ),
    }

    downloaded_contents: dict[str, bytes] = {}

    for result_name, url in download_urls.items():
        response = client.get(url)

        assert response.status_code == 200, response.text
        assert response.content
        assert response.headers["content-type"] == "application/octet-stream"

        downloaded_contents[result_name] = response.content

    pdb_content = downloaded_contents["pdb"].decode("utf-8")
    cif_content = downloaded_contents["cif"].decode("utf-8")

    pdb_structure = read_pdb_string(pdb_content)
    cif_structure = make_structure_from_block(cif.read_string(cif_content).sole_block())

    assert pdb_structure
    assert cif_structure

    pdb_atoms, pdb_atoms_by_serial = get_atoms(pdb_structure)
    cif_atoms, cif_atoms_by_serial = get_atoms(cif_structure)

    assert pdb_atoms, "Generated pdb structure contains no beads"
    assert cif_atoms, "Generated cif structure contains no beads"
    assert pdb_atoms.keys() == cif_atoms.keys(), "Atom keys mismatch"

    for key, pdb_atom in pdb_atoms.items():
        cif_atom = cif_atoms[key]
        assert pdb_atom[0] == cif_atom[0], f"Different element: {key}"
        assert pdb_atom[1:] == pytest.approx(
            cif_atom[1:],
            abs=0.001,
            rel=0,
        ), f"Different coordinates: {key}"

    pdb_connections: set[frozenset[AtomKey]] = set()
    for atom_serial, connected_atoms_serials in pdb_structure.conect_map.items():
        atom_key = pdb_atoms_by_serial[atom_serial]
        for connected_atom_serial in connected_atoms_serials:
            connected_atom_key = pdb_atoms_by_serial[connected_atom_serial]
            connection = frozenset([atom_key, connected_atom_key])
            pdb_connections.add(connection)

    cif_connections = set[frozenset[AtomKey]]()
    for connection in cif_structure.connections:  # type: ignore
        atom1 = cif_structure[0].find_cra(connection.partner1).atom  # type: ignore
        atom2 = cif_structure[0].find_cra(connection.partner2).atom  # type: ignore

        assert atom1 is not None, f"Missing atom: {connection.partner1}"  # type: ignore
        assert atom2 is not None, f"Missing atom: {connection.partner2}"  # type: ignore

        key1 = cif_atoms_by_serial[atom1.serial]
        key2 = cif_atoms_by_serial[atom2.serial]
        cif_connections.add(frozenset((key1, key2)))

    assert pdb_connections, "CG PDB contains no connections"
    assert cif_connections, "CG CIF contains no connections"

    assert pdb_connections == cif_connections, (
        f"Connections only in PDB: {pdb_connections - cif_connections}\n"
        f"Connections only in CIF: {cif_connections - pdb_connections}"
    )
