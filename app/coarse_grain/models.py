from __future__ import annotations

import copy
import json
import logging
import pathlib
from abc import ABC, abstractmethod
from typing import Callable

from gemmi import (
    Asu,
    Atom,
    Chain,
    Connection,
    ConnectionList,
    ConnectionType,
    Element,
    Position,
    Residue,
    Structure,
)

from app.coarse_grain.geometry import (
    calculate_center_of_mass,
    calculate_geometric_center,
)
from app.settings import COARSE_GRAIN_MODELS_DIR

logger = logging.getLogger(__name__)

EMPTY_ALTLOC = "\x00"
PRIMARY_ATOM_ALTLOC = "A"


class CoarseGrainModelRegistry:
    """
    Singleton registry to store RNA model classes.
    """

    _registry: dict[str, type[BaseCoarseGrainModel]] = {}

    @classmethod
    def register(
        cls, model_cls: type[BaseCoarseGrainModel]
    ) -> type[BaseCoarseGrainModel]:
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
    _cached_nucleotide_config: dict | None = None

    DEFAULT_INTER_TAIL = "A2"
    DEFAULT_INTER_HEAD = "A1"

    def read_json_model(self) -> dict | None:
        if self._cached_model_data is None:
            if not self.JSON_model_file or not self.JSON_model_file.exists():
                raise FileNotFoundError(f"Model file not found: {self.JSON_model_file}")

            with open(self.JSON_model_file, "r", encoding="utf-8") as f:
                self._cached_model_data = json.load(f)

        return self._cached_model_data

    @property
    def config(self) -> dict:
        config = self.read_json_model()
        if not config:
            raise ValueError("Configuration is missing.")
        return config

    @property
    def nucleotides_config(self) -> dict:
        if self._cached_nucleotide_config is None:
            self._cached_nucleotide_config = self._build_nucleotide_config()
            for res in self._cached_nucleotide_config.keys():
                self._cached_nucleotide_config[res]["allowed_atoms"] = list(
                    self._cached_nucleotide_config[res]["bead_names"].values()
                )
        return self._cached_nucleotide_config

    def _build_nucleotide_config(self):
        nucleotides_map = {}
        for res in self.config["default_mapping"]["residues"]:
            nucleotides_map[res] = copy.deepcopy(
                self.config["default_mapping"]["config"]
            )

        if self.config.get("mapping") is not None:
            for map in self.config["mapping"]:
                for res in map["residues"]:
                    for config_name, config_values in map["config"].items():
                        for k, v in config_values.items():
                            nucleotides_map[res][config_name][k] = v

        return nucleotides_map

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

    def get_coarse_grain_structure(self, original_structure: Structure) -> Structure:
        coarse_structure = original_structure.clone()
        coarse_structure.connections = ConnectionList()

        self._filter_atoms(coarse_structure)
        self._rebuild_connectivity(coarse_structure)

        coarse_structure.setup_entities()
        return coarse_structure

    def _get_bead_name_for_bead_id(self, res_name: str, bead_id: str) -> str:
        return self.nucleotides_config[res_name]["bead_names"][bead_id]

    def _should_keep_residue(self, residue_name: str) -> bool:
        return residue_name in list(self.nucleotides_config.keys())

    def _filter_atoms(self, structure: Structure) -> None:
        for model in structure:
            for chain in model:
                for res_id in range(len(chain) - 1, -1, -1):
                    res = chain[res_id]

                    if not self._should_keep_residue(res.name):
                        del chain[res_id]
                        continue

                    self._filter_alternate_conformations(res)
                    self._filter_residue_atoms(
                        res, self.nucleotides_config[res.name]["allowed_atoms"]
                    )

        structure.remove_empty_chains()
        structure.assign_serial_numbers(numbered_ter=False)

    def _filter_alternate_conformations(self, residue: Residue) -> None:
        for atom_id in range(len(residue) - 1, -1, -1):
            if (
                residue[atom_id].altloc != EMPTY_ALTLOC
                and residue[atom_id].altloc != PRIMARY_ATOM_ALTLOC
            ):
                del residue[atom_id]
                continue
            residue[atom_id].altloc = EMPTY_ALTLOC

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
            if not self._should_keep_residue(res.name):
                prev_res = None
                continue

            self._add_intra_residue_connections(structure, res, intra_rules, chain.name)

            if prev_res is not None:
                self._add_inter_residue_connection(
                    structure, prev_res, res, inter_rule, chain.name
                )

            prev_res = res

    def _add_intra_residue_connections(
        self, structure: Structure, res: Residue, intra_rules: list, chain_name: str
    ) -> None:
        current_atoms = {atom.name: atom for atom in res}

        for bead_a, bead_b in intra_rules:
            atom_a_name = self._get_bead_name_for_bead_id(res.name, bead_a)
            atom_b_name = self._get_bead_name_for_bead_id(res.name, bead_b)
            if atom_a_name in current_atoms and atom_b_name in current_atoms:
                conn = self._create_connection(
                    res,
                    current_atoms[atom_a_name],
                    res,
                    current_atoms[atom_b_name],
                    chain_name,
                    True,
                )
                structure.connections.append(conn)
                structure.add_conect(
                    current_atoms[atom_a_name].serial,
                    current_atoms[atom_b_name].serial,
                    order=1,
                )
                continue

    def _add_inter_residue_connection(
        self,
        structure: Structure,
        prev_res: Residue,
        curr_res: Residue,
        inter_rule: dict[str, str],
        chain_name: str,
    ) -> None:
        tail_atom_name = self._get_bead_name_for_bead_id(
            prev_res.name, inter_rule["tail"]
        )
        head_atom_name = self._get_bead_name_for_bead_id(
            curr_res.name, inter_rule["head"]
        )

        tail_atom = next((a for a in prev_res if a.name == tail_atom_name), None)
        head_atom = next((a for a in curr_res if a.name == head_atom_name), None)

        if tail_atom and head_atom:
            conn = self._create_connection(
                prev_res, tail_atom, curr_res, head_atom, chain_name
            )
            structure.connections.append(conn)
            structure.add_conect(tail_atom.serial, head_atom.serial, order=1)

    def _create_connection(
        self,
        res1: Residue,
        atom1: Atom,
        res2: Residue,
        atom2: Atom,
        chain_name: str,
        is_intra: bool = False,
    ) -> Connection:
        conn = Connection()
        conn.type = ConnectionType.Covale
        conn.partner1.atom_name = atom1.name
        conn.partner1.chain_name = chain_name
        conn.partner1.res_id.name = res1.name
        conn.partner1.res_id.segment = res1.segment
        conn.partner1.res_id.seqid = res1.seqid

        conn.partner2.atom_name = atom2.name
        conn.partner2.chain_name = chain_name
        conn.partner2.res_id.name = res2.name
        conn.partner2.res_id.segment = res2.segment
        conn.partner2.res_id.seqid = res2.seqid

        if is_intra:
            conn.asu = Asu.Same

        return conn


class CalculateBeadModel(BaseCoarseGrainModel):
    @property
    @abstractmethod
    def center_calculator(self) -> Callable[[Residue, list[str]], Position | None]:
        """Return the function used to calculate bead center positions."""
        ...

    def _filter_atoms(self, structure: Structure) -> None:
        for model in structure:
            for chain in model:
                for res_id in range(len(chain) - 1, -1, -1):
                    res = chain[res_id]

                    if not self._should_keep_residue(res.name):
                        del chain[res_id]
                        continue

                    self._filter_alternate_conformations(res)
                    self._get_residue_with_beads(res)

        structure.remove_empty_chains()
        structure.assign_serial_numbers(numbered_ter=True)

    def _get_residue_with_beads(self, res: Residue) -> Residue:
        res_clone = res.clone()

        for i in range(len(res) - 1, -1, -1):
            del res[i]

        for bead_id, atom_name in self.nucleotides_config[res.name][
            "bead_names"
        ].items():
            atoms = self._get_atoms_for_bead(bead_id, res_clone)
            if not atoms:
                continue

            new_pos = self.center_calculator(res_clone, atoms)
            if new_pos:
                new_atom = Atom()
                new_atom.pos = new_pos
                new_atom.name = atom_name
                new_atom.element = Element("C")
                res.add_atom(new_atom)
        return res_clone

    def _get_atoms_for_bead(self, bead_id: str, residue: Residue) -> list[str]:
        return self.nucleotides_config[residue.name]["atom_centers"][bead_id]


class GeometricCenterModel(CalculateBeadModel):
    """Model that calculates bead positions using geometric center of atoms."""

    @property
    def center_calculator(self) -> Callable[[Residue, list[str]], Position | None]:
        return calculate_geometric_center


class MassCenterModel(CalculateBeadModel):
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
class RNAJPModel(BaseCoarseGrainModel):
    name_verbose: str = "RNA-JP"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "rnajp.json"


@CoarseGrainModelRegistry.register
class FebModel(BaseCoarseGrainModel):
    name_verbose: str = "FebRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "feb_rna.json"


@CoarseGrainModelRegistry.register
class VFoldModel(BaseCoarseGrainModel):
    name_verbose: str = "VFold"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "v_fold.json"


@CoarseGrainModelRegistry.register
class Nares2PModel(GeometricCenterModel):
    name_verbose: str = "Nares-2P"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "nares.json"

    INTER_P_BEAD_NAME = "PP"

    def _calculate_inter_p_bead_position(
        self, curr_res: Residue, prev_res: Residue
    ) -> None:
        atom_id_to_alter = None
        curr_res_sugar_id = None
        prev_res_sugar_id = None
        for atom_id in range(len(curr_res)):
            if curr_res[atom_id].name == "P":
                atom_id_to_alter = atom_id
            elif curr_res[atom_id].name == "S":
                curr_res_sugar_id = atom_id

        for atom_id in range(len(prev_res)):
            if prev_res[atom_id].name == "S":
                prev_res_sugar_id = atom_id

        if (
            atom_id_to_alter is None
            or curr_res_sugar_id is None
            or prev_res_sugar_id is None
        ):
            return

        curr_res[atom_id_to_alter].pos = calculate_geometric_center(
            [curr_res[curr_res_sugar_id], prev_res[prev_res_sugar_id]],
            [curr_res[curr_res_sugar_id].name, prev_res[prev_res_sugar_id].name],
        )  # type: ignore

    def _add_inter_residue_connection(
        self,
        structure: Structure,
        prev_res: Residue,
        curr_res: Residue,
        inter_rule: dict[str, str],
        chain_name: str,
    ) -> None:
        self._calculate_inter_p_bead_position(curr_res, prev_res)

        tail_atom_name = self._get_bead_name_for_bead_id(
            prev_res.name, inter_rule["tail"]
        )
        head_atom_name = self._get_bead_name_for_bead_id(
            curr_res.name, inter_rule["head"]
        )

        tail_atom = next((a for a in prev_res if a.name == tail_atom_name), None)
        head_atom = next((a for a in curr_res if a.name == head_atom_name), None)

        if tail_atom and head_atom:
            structure.add_conect(tail_atom.serial, head_atom.serial, order=1)
            conn = self._create_connection(
                prev_res, tail_atom, curr_res, head_atom, chain_name
            )
            structure.connections.append(conn)


@CoarseGrainModelRegistry.register
class TopRNAModel(GeometricCenterModel):
    name_verbose: str = "TopRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "toprna.json"


@CoarseGrainModelRegistry.register
class IFoldRNAModel(MassCenterModel):
    name_verbose: str = "iFoldRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "ifoldrna.json"


@CoarseGrainModelRegistry.register
class IsRNAOneModel(MassCenterModel):
    name_verbose: str = "isRNA1"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "is_rna_one.json"

    def get_intra_rules(self, residue_name: str) -> list[str]:
        if residue_name in ["A", "G"]:
            return self.config["connectivity"]["intra_residue"]["purine"]
        return self.config["connectivity"]["intra_residue"]["pyrimidine"]

    def _add_intra_residue_connections(
        self,
        structure: Structure,
        res: Residue,
        intra_rules: list[str],
        chain_name: str,
    ) -> None:
        current_atoms = {atom.name: atom for atom in res}

        for bead_a, bead_b in self.get_intra_rules(res.name):
            atom_a_name = self._get_bead_name_for_bead_id(res.name, bead_a)
            atom_b_name = self._get_bead_name_for_bead_id(res.name, bead_b)
            if atom_a_name in current_atoms and atom_b_name in current_atoms:
                conn = self._create_connection(
                    res,
                    current_atoms[atom_a_name],
                    res,
                    current_atoms[atom_b_name],
                    chain_name,
                    True,
                )
                structure.connections.append(conn)
                structure.add_conect(
                    current_atoms[atom_a_name].serial,
                    current_atoms[atom_b_name].serial,
                    order=1,
                )


@CoarseGrainModelRegistry.register
class IsRNATwoModel(MassCenterModel):
    name_verbose: str = "isRNA2"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "is_rna_two.json"


@CoarseGrainModelRegistry.register
class HireModel(MassCenterModel):
    name_verbose: str = "HiRE-RNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "hire_rna.json"

    def get_intra_rules(self, residue_name: str) -> list[str]:
        if residue_name in ["A", "G"]:
            return self.config["connectivity"]["intra_residue"]["purine"]
        return self.config["connectivity"]["intra_residue"]["pyrimidine"]

    def _add_intra_residue_connections(
        self,
        structure: Structure,
        res: Residue,
        intra_rules: list[str],
        chain_name: str,
    ) -> None:
        current_atoms = {atom.name: atom for atom in res}

        for bead_a, bead_b in self.get_intra_rules(res.name):
            atom_a_name = self._get_bead_name_for_bead_id(res.name, bead_a)
            atom_b_name = self._get_bead_name_for_bead_id(res.name, bead_b)
            if atom_a_name in current_atoms and atom_b_name in current_atoms:
                conn = self._create_connection(
                    res,
                    current_atoms[atom_a_name],
                    res,
                    current_atoms[atom_b_name],
                    chain_name,
                    True,
                )
                structure.connections.append(conn)
                structure.add_conect(
                    current_atoms[atom_a_name].serial,
                    current_atoms[atom_b_name].serial,
                    order=1,
                )
