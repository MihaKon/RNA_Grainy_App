from __future__ import annotations

import json
import pathlib
from abc import ABC

from gemmi import Connection, ConnectionType, Selection, Structure

from app.settings import COARSE_GRAIN_MODELS_DIR


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

    def read_json_model(self) -> dict:
        if self._cached_model_data is None:
            if not self.JSON_model_file or not self.JSON_model_file.exists():
                raise FileNotFoundError(f"Model file not found: {self.JSON_model_file}")

            with open(self.JSON_model_file, "r") as f:
                self._cached_model_data = json.load(f)

        assert self._cached_model_data is not None
        return self._cached_model_data

    def get_atoms_subset_mapping(self) -> dict[str, list]:
        model_data = self.read_json_model()
        mapping = model_data.get("mapping", [])
        allowed_atoms = {}
        for group in mapping.values():
            for res_name in group["residues"]:
                allowed_atoms[res_name] = list(group["atoms"].values())
        return allowed_atoms

    def get_coarse_grain_structure(self, original_structure: Structure) -> Structure:
        """Apply coarse-graining to the structure and rebuild connections from the map."""

        config = self.read_json_model()
        mapping_config = config["mapping"]

        res_type_map = {}
        for g_name, g_data in mapping_config.items():
            for r_name in g_data["residues"]:
                res_type_map[r_name] = g_name

        coarse_structure = original_structure.clone()
        coarse_structure.clear_conect()

        allowed_atoms = self.get_atoms_subset_mapping()

        for model in coarse_structure:
            for chain in model:
                for res_id in range(len(chain) - 1, -1, -1):
                    res = chain[res_id]
                    if res.name not in allowed_atoms:
                        del chain[res_id]
                        continue

                    keep_list = set(allowed_atoms[res.name])
                    for atom_id in range(len(res) - 1, -1, -1):
                        if res[atom_id].name not in keep_list:
                            del res[atom_id]

        coarse_structure.remove_empty_chains()
        coarse_structure.assign_serial_numbers(numbered_ter=True)

        intra_rules = config["connectivity"]["intra_residue"]
        inter_rules_config = config["connectivity"].get("inter_residue", [])

        inter_rule_tail = "A2"
        inter_rule_head = "A1"

        if inter_rules_config:
            rule = inter_rules_config[0]
            val_source = rule.get("source")
            val_target = rule.get("target")

            inter_rule_tail = val_source
            inter_rule_head = val_target

        for model in coarse_structure:
            for chain in model:
                prev_res = None

                for res in chain:
                    r_type = res_type_map.get(res.name)
                    if not r_type:
                        prev_res = None
                        continue

                    atom_map = mapping_config[r_type]["atoms"]
                    current_atoms = {atom.name: atom for atom in res}

                    for bead_a, bead_b in intra_rules:
                        name_a = atom_map.get(bead_a)
                        name_b = atom_map.get(bead_b)

                        if name_a in current_atoms and name_b in current_atoms:
                            coarse_structure.connections.append(
                                self._get_connection(
                                    res,
                                    current_atoms[name_a],
                                    res,
                                    current_atoms[name_b],
                                )
                            )

                    if prev_res is not None:
                        prev_type = res_type_map.get(prev_res.name)
                        prev_atom_map = mapping_config[prev_type]["atoms"]

                        tail_atom_name = prev_atom_map.get(inter_rule_tail)
                        head_atom_name = atom_map.get(inter_rule_head)

                        tail_atom = next(
                            (a for a in prev_res if a.name == tail_atom_name), None
                        )
                        head_atom = current_atoms.get(head_atom_name)

                        if tail_atom and head_atom:
                            coarse_structure.connections.append(
                                self._get_connection(
                                    prev_res, tail_atom, res, head_atom
                                )
                            )

                    prev_res = res

        coarse_structure.setup_entities()
        coarse_structure.assign_label_seq_id()
        return coarse_structure

    def _get_connection(self, res1, atom1, res2, atom2):
        """Helper to create and append a gemmi connection."""
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
class Nares2PModel(BaseCoarseGrainModel):
    name_verbose: str = "Nares-2P"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "nares.json"


@CoarseGrainModelRegistry.register
class IFoldRNAModel(BaseCoarseGrainModel):
    name_verbose: str = "iFoldRNA"
    JSON_model_file: pathlib.Path = COARSE_GRAIN_MODELS_DIR / "ifoldrna.json"


@CoarseGrainModelRegistry.register
class TopRNAModel(BaseCoarseGrainModel):
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
class SPQRModel(BaseCoarseGrainModel):
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
