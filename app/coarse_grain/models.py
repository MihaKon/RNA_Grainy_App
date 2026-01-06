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


class MassCenterModel(CalculatedBeadModel):
    """Model that calculates bead positions using center of mass of atoms."""

    @property
    def center_calculator(self) -> Callable[[Residue, list[str]], Position | None]:
        return calculate_center_of_mass


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


@CoarseGrainModelRegistry.register
class IFoldRNAModel(BaseCoarseGrainModel):
    name_verbose: str = "iFoldRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "ifoldrna.json"


@CoarseGrainModelRegistry.register
class TopRNAModel(GeometricCenterModel):
    name_verbose: str = "TopRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "toprna.json"


@CoarseGrainModelRegistry.register
class IsRNAOneModel(BaseCoarseGrainModel):
    name_verbose: str = "IsRNA1"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "is_rna_one.json"


@CoarseGrainModelRegistry.register
class IsRNATwoModel(BaseCoarseGrainModel):
    name_verbose: str = "IsRNA2"
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
class HireModel(BaseCoarseGrainModel):
    name_verbose: str = "HireRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "hire_rna.json"


@CoarseGrainModelRegistry.register
class OxModel(BaseCoarseGrainModel):
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
