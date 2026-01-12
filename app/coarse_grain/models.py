from __future__ import annotations

import json
import logging
import pathlib
from abc import ABC, abstractmethod
from typing import Callable

from gemmi import (
    Atom,
    Chain,
    Connection,
    ConnectionType,
    Element,
    Position,
    Residue,
    Structure,
)

from app.coarse_grain.geometry import (
    NUCLEOTIDE_ATOMS,
    calculate_center_of_mass,
    calculate_geometric_center,
    get_base_atoms,
)
from app.settings import COARSE_GRAIN_MODELS_DIR

logger = logging.getLogger(__name__)


class CoarseGrainModelRegistry:
    """
    Singleton registry to store RNA model classes.
    """

    _registry: dict[str, type[BaseCoarseGrainModel]] = {}

    @classmethod
    def register(cls, model_cls: type[BaseCoarseGrainModel]):
        cls._registry[model_cls.__name__] = model_cls
        return model_cls

    @classmethod
    def get_model(cls, class_name: str) -> type[BaseCoarseGrainModel]:
        if class_name not in cls._registry:
            available = list(cls._registry.keys())
            raise KeyError(
                f"Model '{class_name}' not found. Available models: {available}"
            )
        return cls._registry[class_name]

    @classmethod
    def get_dropdown_options(cls) -> list[tuple[str, str]]:
        return sorted(
            [(key, model_cls.name_verbose) for key, model_cls in cls._registry.items()],
            key=lambda x: x[1],
        )


class BaseCoarseGrainModel(ABC):
    name_verbose: str
    JSON_model_file: pathlib.Path
    _cached_model_data: dict | None = None
    _cached_residue_type_map: dict[str, str] | None = None
    _cached_allowed_atoms: dict[str, list[str]] | None = None

    DEFAULT_INTER_TAIL = "A2"
    DEFAULT_INTER_HEAD = "A1"

    @property
    def config(self) -> dict | None:
        return self.read_json_model()

    @property
    def mapping_config(self) -> dict:
        mapping = self.config.get("mapping")
        if not mapping:
            raise ValueError("Configuration missing required 'mapping' section")
        return mapping

    @property
    def residue_type_map(self) -> dict[str, str]:
        if self._cached_residue_type_map is None:
            self._cached_residue_type_map = self._build_residue_type_map()
        return self._cached_residue_type_map

    @property
    def connectivity_rules(self) -> tuple[list, dict]:
        conn = self.config.get("connectivity")
        if not conn:
            raise ValueError("Configuration missing required 'connectivity' section")

        intra = conn.get("intra_residue", [])
        inter_config = conn.get("inter_residue", [])

        inter_rule = {"tail": self.DEFAULT_INTER_TAIL, "head": self.DEFAULT_INTER_HEAD}

        if inter_config:
            rule_data = inter_config[0]
            inter_rule["tail"] = rule_data.get("source", self.DEFAULT_INTER_TAIL)
            inter_rule["head"] = rule_data.get("target", self.DEFAULT_INTER_HEAD)

        return intra, inter_rule

    @property
    def allowed_atoms_map(self) -> dict[str, list[str]]:
        if self._cached_allowed_atoms is None:
            self._cached_allowed_atoms = self._build_allowed_atoms_map()
        return self._cached_allowed_atoms

    def read_json_model(self) -> dict | None:
        if self._cached_model_data is None:
            if not self.JSON_model_file or not self.JSON_model_file.exists():
                raise FileNotFoundError(f"Model file not found: {self.JSON_model_file}")

            with open(self.JSON_model_file, "r", encoding="utf-8") as f:
                self._cached_model_data = json.load(f)

        return self._cached_model_data

    def _build_residue_type_map(self) -> dict[str, str]:
        res_map = {}
        for group_name, group_data in self.mapping_config.items():
            for res_name in group_data["residues"]:
                res_map[res_name] = group_name
        return res_map

    def _build_allowed_atoms_map(self) -> dict[str, list[str]]:
        allowed_atoms = {}
        for group in self.mapping_config.values():
            for res_name in group["residues"]:
                allowed_atoms[res_name] = list(group["atoms"].values())
        return allowed_atoms

    def _get_atom_name_for_bead(self, res_type: str, bead_id: str) -> str:
        return self.mapping_config[res_type]["atoms"][bead_id]

    def _should_keep_residue(self, residue_name: str) -> bool:
        return residue_name in self.allowed_atoms_map

    def get_coarse_grain_structure(self, original_structure: Structure) -> Structure:
        coarse_structure = original_structure.clone()
        coarse_structure.clear_conect()

        self._filter_atoms(coarse_structure)
        self._rebuild_connectivity(coarse_structure)

        coarse_structure.setup_entities()
        coarse_structure.assign_label_seq_id()
        return coarse_structure

    def _filter_atoms(self, structure: Structure) -> None:
        allowed_atoms = self.allowed_atoms_map

        for model in structure:
            for chain in model:
                for res_id in range(len(chain) - 1, -1, -1):
                    res = chain[res_id]

                    if not self._should_keep_residue(res.name):
                        del chain[res_id]
                        continue

                    self._filter_residue_atoms(res, allowed_atoms[res.name])

        structure.remove_empty_chains()
        structure.assign_serial_numbers(numbered_ter=True)

    def _filter_residue_atoms(
        self, residue: Residue, allowed_atom_names: list[str]
    ) -> None:
        keep_set = set(allowed_atom_names)
        for atom_id in range(len(residue) - 1, -1, -1):
            if residue[atom_id].name not in keep_set:
                del residue[atom_id]

    def _rebuild_connectivity(self, structure: Structure) -> None:
        intra_rules, inter_rule = self.connectivity_rules

        for model in structure:
            for chain in model:
                self._connect_chain_residues(structure, chain, intra_rules, inter_rule)

    def _connect_chain_residues(
        self, structure: Structure, chain: Chain, intra_rules: list, inter_rule: dict
    ) -> None:
        prev_res = None

        for res in chain:
            res_type = self.residue_type_map.get(res.name)
            if not res_type:
                prev_res = None
                continue

            self._add_intra_residue_connections(structure, res, res_type, intra_rules)

            if prev_res is not None:
                self._add_inter_residue_connection(structure, prev_res, res, inter_rule)

            prev_res = res

    def _add_intra_residue_connections(
        self, structure: Structure, res: Residue, res_type: str, intra_rules: list
    ) -> None:
        current_atoms = {atom.name: atom for atom in res}

        for bead_a, bead_b in intra_rules:
            atom_a_name = self._get_atom_name_for_bead(res_type, bead_a)
            atom_b_name = self._get_atom_name_for_bead(res_type, bead_b)
            if atom_a_name in current_atoms and atom_b_name in current_atoms:
                conn = self._create_connection(
                    res, current_atoms[atom_a_name], res, current_atoms[atom_b_name]
                )
                structure.connections.append(conn)

    def _add_inter_residue_connection(
        self,
        structure: Structure,
        prev_res: Residue,
        curr_res: Residue,
        inter_rule: dict,
    ) -> None:
        prev_type: str = self.residue_type_map.get(prev_res.name, "")
        curr_type: str = self.residue_type_map.get(curr_res.name, "")

        tail_atom_name = self._get_atom_name_for_bead(prev_type, inter_rule["tail"])
        head_atom_name = self._get_atom_name_for_bead(curr_type, inter_rule["head"])

        tail_atom = next((a for a in prev_res if a.name == tail_atom_name), None)
        head_atom = next((a for a in curr_res if a.name == head_atom_name), None)

        if tail_atom and head_atom:
            conn = self._create_connection(prev_res, tail_atom, curr_res, head_atom)
            structure.connections.append(conn)

    def _create_connection(
        self, res1: Residue, atom1: Atom, res2: Residue, atom2: Atom
    ) -> Connection:
        conn = Connection()
        conn.type = ConnectionType.Covale
        conn.partner1.atom_name = atom1.name
        conn.partner1.chain_name = (
            res1.chain_name if hasattr(res1, "chain_name") else res1.subchain
        )
        conn.partner1.res_id.name = res1.name
        conn.partner1.res_id.segment = res1.segment
        conn.partner1.res_id.seqid = res1.seqid

        conn.partner2.atom_name = atom2.name
        conn.partner2.chain_name = (
            res2.chain_name if hasattr(res2, "chain_name") else res2.subchain
        )
        conn.partner2.res_id.name = res2.name
        conn.partner2.res_id.segment = res2.segment
        conn.partner2.res_id.seqid = res2.seqid

        return conn


class CalculatedBeadModel(BaseCoarseGrainModel):
    """
    Base class for coarse-grain models that calculate bead positions from atom groups.

    This class handles models where bead positions are computed by aggregating
    coordinates of multiple atoms (e.g., geometric center or center of mass),
    rather than directly mapping to existing atom positions.

    Subclasses must implement `center_calculator` to specify the aggregation method.

    CIF Output Format Reference:
        Column layout for generated ATOM records:
        1: Record type (ATOM)
        2: Serial number
        3: Element symbol
        4: Atom name (bead type: P, S, B)
        5: Alt location indicator
        6: Residue name (label_comp_id) - from original structure
        7: Chain ID (label_asym_id) - from original structure
        8: Entity ID
        9: Residue sequence number (label_seq_id) - from original structure
        10: Insertion code

        Example output:
        ATOM 1 C S . U A 1 1 ? 12.266 12.155 24.322 1 20 ? 1 A 1
    """

    @property
    @abstractmethod
    def center_calculator(self) -> Callable[[Residue, list[str]], Position | None]:
        """Return the function used to calculate bead center positions."""
        ...

    def _should_keep_residue(self, residue_name: str) -> bool:
        return residue_name in ["A", "C", "G", "U"]

    def get_coarse_grain_structure(self, original_structure: Structure) -> Structure:
        coarse_structure: Structure = self._create_coarse_grain_atoms(
            original_structure
        )
        self._remove_empty_chains(coarse_structure)
        self._rebuild_cg_structure(original_structure, coarse_structure)
        self._filter_atoms(coarse_structure)
        self._rebuild_connectivity(coarse_structure)
        coarse_structure.setup_entities()
        self._assign_label_seq_ids(coarse_structure)
        return coarse_structure

    def _rebuild_cg_structure(
        self, original_structure: Structure, coarse_structure: Structure
    ) -> None:
        """Fix CIF labels to match original structure for Molstar compatibility."""
        orig_models = list(original_structure)
        cg_models = list(coarse_structure)

        for orig_model, cg_model in zip(orig_models, cg_models):
            for orig_chain, cg_chain in zip(orig_model, cg_model):
                orig_res_list = list(orig_chain)
                cg_res_list = list(cg_chain)
                limit = min(len(orig_res_list), len(cg_res_list))

                for i in range(limit):
                    orig_res = orig_res_list[i]
                    cg_res = cg_res_list[i]
                    cg_res.name = orig_res.name
                    cg_res.subchain = orig_chain.name

    def _assign_label_seq_ids(self, structure: Structure) -> None:
        """Assign label_seq_id so beads map to original residue numbers."""
        for model in structure:
            for chain in model:
                for residue in chain:
                    residue.label_seq = residue.seqid.num

    def _create_coarse_grain_atoms(self, original_structure: Structure) -> Structure:
        """Create a coarse-grain Structure by computing bead positions for residues.

        For each model/chain/residue in `original_structure`, a corresponding `Residue`
        is created in the coarse-grain structure containing bead `Atom` objects. Beads
        are computed only for residues where `_should_keep_residue` returns True. The
        bead positions are determined by the model's `center_calculator` and bead
        names are taken from the mapping configuration. The returned structure preserves
        metadata such as `seqid` and `segment` so it can be mapped back to the original
        structure for CIF output and connectivity reconstruction.
        """
        coarse_structure = original_structure.clone()
        for model in coarse_structure:
            for chain in list(model):
                model.remove_chain(chain.name)

        coarse_structure.clear_conect()
        for model in original_structure:
            cg_model = coarse_structure[0]
            for chain in model:
                cg_chain = Chain(chain.name)
                for res in chain:
                    if not self._should_keep_residue(res.name):
                        continue

                    cg_res = Residue()
                    cg_res.name = res.name
                    cg_res.seqid = res.seqid
                    cg_res.segment = res.segment

                    self._generate_beads(res, cg_res)
                    logger.debug(
                        "Generated %d beads for residue %s%s",
                        len(cg_res),
                        res.name,
                        res.seqid,
                    )

                    if len(cg_res) > 0:
                        cg_chain.add_residue(cg_res)
                if len(cg_chain) > 0:
                    cg_model.add_chain(cg_chain)
        return coarse_structure

    def _generate_beads(self, source: Residue, target: Residue) -> None:
        """Generate bead Atoms for a target residue from source residue atoms.

        Looks up beads defined for the residue type and, for each bead ID, gathers the
        atom names to use via `_get_atoms_for_bead`. The bead position is computed by
        calling `self.center_calculator` with the source residue and the list of atom
        names. If a Position is returned an `Atom` is created (element 'C') with the
        configured output name and appended to `target`.

        Missing residue type mappings or empty atom lists are silently skipped and a
        warning is logged when the residue type can't be found in the model mapping.
        """
        res_type = self.residue_type_map.get(source.name)
        if not res_type:
            logger.warning(
                "Residue type for %s not found in mapping config", source.name
            )
            return

        bead_definitions = self.mapping_config[res_type]["atoms"]

        for bead_id, atom_name in bead_definitions.items():
            atoms = self._get_atoms_for_bead(bead_id, source)
            if not atoms:
                continue

            new_pos = self.center_calculator(source, atoms)
            if new_pos:
                new_atom = Atom()
                new_atom.name = atom_name
                new_atom.element = Element("C")
                new_atom.pos = new_pos
                target.add_atom(new_atom)

    def _get_atoms_for_bead(self, bead_id: str, residue: Residue) -> list[str]:
        """Return a list of atom names used to compute a bead center.

        The mapping is model-specific and uses common nucleotide groups:
        - 'A1' -> phosphate atoms (e.g., P, OP1, OP2)
        - 'A2' -> sugar atoms (ribose)
        - 'A3' -> base atoms (depends on residue identity)
        Returns an empty list for unknown bead IDs.
        """
        if bead_id == "A1":
            return NUCLEOTIDE_ATOMS["phosphate"]
        elif bead_id == "A2":
            return NUCLEOTIDE_ATOMS["sugar"]
        elif bead_id == "A3":
            return get_base_atoms(residue.name)
        return []

    def _remove_empty_chains(self, structure: Structure) -> None:
        for model in structure:
            chains_to_remove = [chain.name for chain in model if len(chain) == 0]
            for chain_name in chains_to_remove:
                model.remove_chain(chain_name)

    def _rebuild_connectivity(self, structure: Structure) -> None:
        intra_rules, inter_rule = self.connectivity_rules
        for model in structure:
            for chain in model:
                self._connect_chain_residues(structure, chain, intra_rules, inter_rule)


class GeometricCenterModel(CalculatedBeadModel):
    """Model that calculates bead positions using geometric center of atoms."""

    @property
    def center_calculator(self) -> Callable[[Residue, list[str]], Position | None]:
        return calculate_geometric_center


class MassCenterModel(BaseCoarseGrainModel):
    """
    Model that handles flexible bead definitions from JSON configuration.

    This class supports:
    - Single atom definitions: bead position is taken directly from the atom
    - Multi-atom definitions: bead position is calculated as Center of Mass

    JSON format for atoms field:
    - "A1": "P"                    -> single atom, use P atom position
    - "A1": ["P", "OP1", "OP2"]    -> multi-atom, calculate COM of these atoms
    """

    @property
    def center_calculator(self) -> Callable[[Residue, list[str]], Position | None]:
        """Return the function used to calculate bead center positions for multi-atom beads."""
        return calculate_center_of_mass

    def _should_keep_residue(self, residue_name: str) -> bool:
        return residue_name in ["A", "C", "G", "U"]

    def _get_residue_type(self, residue_name: str) -> str | None:
        """Get the residue type (group name) for a given residue name."""
        return self.residue_type_map.get(residue_name)

    def _get_bead_atom_definition(
        self, res_type: str, bead_id: str
    ) -> str | list[str] | None:
        """
        Get the atom definition for a bead from the mapping config.

        Returns:
        - str: single atom name
        - list[str]: list of atom names for COM calculation
        - None: if bead_id not found
        """
        atoms = self.mapping_config.get(res_type, {}).get("atoms", {})
        return atoms.get(bead_id)

    def _get_bead_name(self, res_type: str, bead_id: str) -> str:
        """
        Get the output bead name for a given bead ID.

        Uses 'bead_names' field if available, otherwise uses the atom definition
        (for single atoms) or the bead_id itself.
        """
        group_config = self.mapping_config.get(res_type, {})
        bead_names = group_config.get("bead_names", {})

        if bead_id in bead_names:
            return bead_names[bead_id]

        atom_def = group_config.get("atoms", {}).get(bead_id)
        if isinstance(atom_def, str):
            return atom_def

        return bead_id

    def _is_single_atom_bead(self, atom_definition: str | list[str]) -> bool:
        """Return True if the bead atom definition is a single atom name.

        A single-atom definition is expressed as a `str`; multi-atom definitions are
        expressed as lists of atom names and require center calculation.
        """
        return isinstance(atom_definition, str)

    def _get_single_atom_position(
        self, residue: Residue, atom_name: str
    ) -> Position | None:
        """Return the Position of `atom_name` in `residue`, or None if not present.

        Used for beads defined by a single atom name in the JSON mapping. The method
        iterates through residue atoms and returns the first matching position.
        """
        for atom in residue:
            if atom.name == atom_name:
                return atom.pos
        return None

    def get_coarse_grain_structure(self, original_structure: Structure) -> Structure:
        coarse_structure: Structure = self._create_coarse_grain_atoms(
            original_structure
        )
        self._remove_empty_chains(coarse_structure)
        self._rebuild_cg_structure(original_structure, coarse_structure)
        self._rebuild_connectivity(coarse_structure)
        coarse_structure.setup_entities()
        self._assign_label_seq_ids(coarse_structure)
        return coarse_structure

    def _rebuild_cg_structure(
        self, original_structure: Structure, coarse_structure: Structure
    ) -> None:
        """Fix CIF labels to match original structure for Molstar compatibility."""
        orig_models = list(original_structure)
        cg_models = list(coarse_structure)

        for orig_model, cg_model in zip(orig_models, cg_models):
            for orig_chain, cg_chain in zip(orig_model, cg_model):
                orig_res_list = list(orig_chain)
                cg_res_list = list(cg_chain)
                limit = min(len(orig_res_list), len(cg_res_list))

                for i in range(limit):
                    orig_res = orig_res_list[i]
                    cg_res = cg_res_list[i]
                    cg_res.name = orig_res.name
                    cg_res.subchain = orig_chain.name

    def _assign_label_seq_ids(self, structure: Structure) -> None:
        """Assign label_seq_id so beads map to original residue numbers."""
        for model in structure:
            for chain in model:
                for residue in chain:
                    residue.label_seq = residue.seqid.num

    def _create_coarse_grain_atoms(self, original_structure: Structure) -> Structure:
        """Create a coarse-grain Structure using JSON bead definitions.

        This variant supports bead definitions that are either a single atom name or
        a list of atom names (computed as a center of mass). Behaves similarly to the
        calculated-bead model: it clones the original structure and builds new chains of
        coarse-grain residues preserving `seqid` and `segment` information for mapping
        and output compatibility.
        """
        coarse_structure = original_structure.clone()
        for model in coarse_structure:
            for chain in list(model):
                model.remove_chain(chain.name)

        coarse_structure.clear_conect()
        for model in original_structure:
            cg_model = coarse_structure[0]
            for chain in model:
                cg_chain = Chain(chain.name)
                for res in chain:
                    if not self._should_keep_residue(res.name):
                        continue

                    cg_res = Residue()
                    cg_res.name = res.name
                    cg_res.seqid = res.seqid
                    cg_res.segment = res.segment

                    self._generate_beads(res, cg_res)
                    logger.debug(
                        "Generated %d beads for residue %s%s",
                        len(cg_res),
                        res.name,
                        res.seqid,
                    )

                    if len(cg_res) > 0:
                        cg_chain.add_residue(cg_res)
                if len(cg_chain) > 0:
                    cg_model.add_chain(cg_chain)
        return coarse_structure

    def _generate_beads(self, source: Residue, target: Residue) -> None:
        """Generate coarse-grained beads for a residue using JSON mapping.

        For each bead ID in the mapping for the residue's group, get the atom
        definition (either a single atom name or a list). For single-atom beads the
        bead position is taken from that atom; for multi-atom beads the position is
        computed via `center_calculator` (center of mass). The output bead name is
        resolved through `_get_bead_name`. If a position is available, an `Atom` is
        created and appended to `target`.
        """
        res_type = self._get_residue_type(source.name)
        if not res_type:
            logger.warning(
                "Residue type for %s not found in mapping config", source.name
            )
            return

        bead_definitions = self.mapping_config[res_type]["atoms"]

        for bead_id in bead_definitions:
            atom_def = self._get_bead_atom_definition(res_type, bead_id)
            if atom_def is None:
                continue

            bead_name = self._get_bead_name(res_type, bead_id)

            if self._is_single_atom_bead(atom_def):
                new_pos = self._get_single_atom_position(source, atom_def)
            else:
                new_pos = self.center_calculator(source, atom_def)

            if new_pos:
                new_atom = Atom()
                new_atom.name = bead_name
                new_atom.element = Element("C")
                new_atom.pos = new_pos
                target.add_atom(new_atom)

    def _remove_empty_chains(self, structure: Structure) -> None:
        for model in structure:
            chains_to_remove = [chain.name for chain in model if len(chain) == 0]
            for chain_name in chains_to_remove:
                model.remove_chain(chain_name)

    def _rebuild_connectivity(self, structure: Structure) -> None:
        intra_rules, inter_rule = self.connectivity_rules
        for model in structure:
            for chain in model:
                self._connect_chain_residues(structure, chain, intra_rules, inter_rule)

    def _get_atom_name_for_bead(self, res_type: str, bead_id: str) -> str:
        """Get the output atom name for a bead (used for connectivity)."""
        return self._get_bead_name(res_type, bead_id)

    def _build_allowed_atoms_map(self) -> dict[str, list[str]]:
        """Build map of residue name to list of allowed output atom names."""
        allowed_atoms = {}
        for group in self.mapping_config.values():
            bead_names = group.get("bead_names", {})
            atoms = group.get("atoms", {})

            output_atoms = []
            for bead_id in atoms:
                if bead_id in bead_names:
                    output_atoms.append(bead_names[bead_id])
                elif isinstance(atoms[bead_id], str):
                    output_atoms.append(atoms[bead_id])
                else:
                    output_atoms.append(bead_id)

            for res_name in group["residues"]:
                allowed_atoms[res_name] = output_atoms

        return allowed_atoms


@CoarseGrainModelRegistry.register
class SimModel(BaseCoarseGrainModel):
    name_verbose: str = "SimRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "simrna.json"


@CoarseGrainModelRegistry.register
class NASTModel(BaseCoarseGrainModel):
    name_verbose: str = "NAST"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "nast.json"


@CoarseGrainModelRegistry.register
class YUPModel(BaseCoarseGrainModel):
    name_verbose: str = "YUP"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "yup.json"


@CoarseGrainModelRegistry.register
class Nares2PModel(GeometricCenterModel):
    name_verbose: str = "Nares-2P"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "nares.json"

    INTER_P_BEAD_NAME = "PP"

    def get_coarse_grain_structure(self, original_structure: Structure) -> Structure:
        coarse_structure = super().get_coarse_grain_structure(original_structure)
        self._add_inter_phosphorus_beads(original_structure, coarse_structure)
        return coarse_structure

    def _add_inter_phosphorus_beads(
        self, original_structure: Structure, coarse_structure: Structure
    ) -> None:
        """Insert inter-residue phosphorus beads between consecutive P atoms.

        For each pair of adjacent residues in a chain that both pass `_should_keep_residue`,
        compute the midpoint of their P atom coordinates and create an `Atom` named
        `INTER_P_BEAD_NAME` with element 'P'. The new bead is attached to the coarse-grain
        residue corresponding to the first of the pair (if available).
        """
        for orig_model, cg_model in zip(original_structure, coarse_structure):
            for _, cg_chain in zip(orig_model, cg_model):
                cg_residues = list(cg_chain)

                for i in range(len(cg_residues) - 1):
                    curr_orig_res = cg_residues[i]
                    next_orig_res = cg_residues[i + 1]

                    if not self._should_keep_residue(
                        curr_orig_res.name
                    ) or not self._should_keep_residue(next_orig_res.name):
                        continue

                    curr_p = self._get_phosphorus_atom(curr_orig_res)
                    next_p = self._get_phosphorus_atom(next_orig_res)

                    if curr_p is None or next_p is None:
                        continue

                    midpoint = Position(
                        (curr_p.pos.x + next_p.pos.x) / 2,
                        (curr_p.pos.y + next_p.pos.y) / 2,
                        (curr_p.pos.z + next_p.pos.z) / 2,
                    )

                    pp_atom = Atom()
                    pp_atom.name = self.INTER_P_BEAD_NAME
                    pp_atom.element = Element("P")
                    pp_atom.pos = midpoint

                    if i < len(cg_residues):
                        cg_residues[i].add_atom(pp_atom)

    def _get_phosphorus_atom(self, residue: Residue) -> Atom | None:
        """Return the phosphorus `Atom` (name 'P') from `residue`, or None if absent.

        Helper used when computing inter-phosphorus midpoint beads; returns the first
        atom whose name equals 'P'.
        """
        for atom in residue:
            if atom.name == "P":
                return atom
        return None


@CoarseGrainModelRegistry.register
class IFoldRNAModel(MassCenterModel):
    name_verbose: str = "iFoldRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "ifoldrna.json"


@CoarseGrainModelRegistry.register
class TopRNAModel(GeometricCenterModel):
    name_verbose: str = "TopRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "toprna.json"


@CoarseGrainModelRegistry.register
class IsRNAOneModel(MassCenterModel):
    name_verbose: str = "isRNA1"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "is_rna_one.json"


@CoarseGrainModelRegistry.register
class IsRNATwoModel(MassCenterModel):
    name_verbose: str = "isRNA2"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "is_rna_two.json"


@CoarseGrainModelRegistry.register
class SPQRModel(GeometricCenterModel):
    name_verbose: str = "SPQR"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "spqr.json"


@CoarseGrainModelRegistry.register
class RNAJPModel(BaseCoarseGrainModel):
    name_verbose: str = "RNAJP"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "rnajp.json"


@CoarseGrainModelRegistry.register
class HireModel(MassCenterModel):
    name_verbose: str = "HiRE-RNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "hire_rna.json"


@CoarseGrainModelRegistry.register
class OxModel(MassCenterModel):
    name_verbose: str = "oxRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "ox_rna.json"


@CoarseGrainModelRegistry.register
class FebModel(BaseCoarseGrainModel):
    name_verbose: str = "FebRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "feb_rna.json"


@CoarseGrainModelRegistry.register
class VFoldModel(BaseCoarseGrainModel):
    name_verbose: str = "VFold"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "v_fold.json"
