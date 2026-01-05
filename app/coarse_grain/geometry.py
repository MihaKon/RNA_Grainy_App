from gemmi import Position, Residue

ATOMIC_MASSES = {
    'H': 1.008,
    'C': 12.011,
    'N': 14.007,
    'O': 15.999,
    'P': 30.974,
    'S': 32.06,
}

NUCLEOTIDE_ATOMS = {
    "phosphate": ["P", "OP1", "OP2", "O1P", "O2P"],
    "sugar": ["C1'", "C2'", "C3'", "C4'", "C5'", "O2'", "O3'", "O4'", "O5'"],
    "purine": ["N1", "C2", "N3", "C4", "C5", "C6", "N7", "C8", "N9"],
    "pyrimidine": ["N1", "C2", "O2", "N3", "C4", "N4", "O4", "C5", "C6"]
}

def get_atomic_mass(atom_name: str, element_name: str = "") -> float:
    el = element_name if element_name else "".join([c for c in atom_name if c.isalpha()])[-1]
    return ATOMIC_MASSES.get(el, ATOMIC_MASSES['C'])

def calculate_center_of_mass(residue: Residue, atom_names: list[str]) -> Position:
    total_mass = 0.0
    x, y, z = 0.0, 0.0, 0.0
    
    for atom in residue:
        if atom.name in atom_names:
            mass = get_atomic_mass(atom.name, atom.element.name)
            x += atom.pos.x * mass
            y += atom.pos.y * mass
            z += atom.pos.z * mass
            total_mass += mass
    
    if total_mass == 0:
        return None
    
    return Position(x / total_mass, y / total_mass, z / total_mass)

def calculate_geometric_center(residue: Residue, atom_names: list[str]) -> Position:
    count = 0.0
    x, y, z = 0.0, 0.0, 0.0

    for atom in residue:
        if atom.name in atom_names:
            x += atom.pos.x
            y += atom.pos.y
            z += atom.pos.z
            count += 1.0

    if count == 0:
        return None
    
    return Position(x / count, y / count, z / count)

def get_base_atoms(res_name: str) -> list[str]:
    name = res_name.upper().strip()
    if name in ["A", "G"]:
        return NUCLEOTIDE_ATOMS["purine"]
    elif name in ["C", "U"]:
        return NUCLEOTIDE_ATOMS["pyrimidine"]
    else:
        return []