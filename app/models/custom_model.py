from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

strict_config = ConfigDict(extra="forbid")

BEAD_STRATEGIES = ("direct", "geometric_center", "center_of_mass")


class MappingConfig(BaseModel):
    model_config = strict_config
    bead_names: dict[str, str]
    atom_centers: dict[str, list[str]]
    description: dict[str, str]
    strategies: dict[str, str]


class MappingEntry(BaseModel):
    model_config = strict_config
    residues: list[str] = Field(min_length=1)
    config: MappingConfig


class InterResidueLink(BaseModel):
    model_config = strict_config
    source: str
    target: str


class Connectivity(BaseModel):
    model_config = strict_config
    intra_residue: list[tuple[str, str]]
    inter_residue: list[InterResidueLink]

    @field_validator("inter_residue")
    @classmethod
    def validate_inter_residue_limit(
        cls, v: list[InterResidueLink]
    ) -> list[InterResidueLink]:
        if len(v) > 1:
            raise ValueError("Only one inter-residue link is supported.")
        return v


class CustomModelDefinition(BaseModel):
    model_config = strict_config
    model_name: str | None = "Custom Model"
    description: str | None = ""
    default_mapping: MappingEntry
    mapping: list[MappingEntry] = []
    connectivity: Connectivity

    @model_validator(mode="after")
    def validate_beads_and_connections(self) -> Self:
        residue_beads = self._resolve_residue_beads()

        if not any(residue_beads.values()):
            raise ValueError("The model defines no beads.")

        for residue, config in self._resolve_residue_configs().items():
            for bead_id in config["bead_names"]:
                if not config["atom_centers"].get(bead_id):
                    raise ValueError(f"Bead {bead_id} of {residue} has no atoms.")
            for bead_id, strategy in config["strategies"].items():
                if strategy not in BEAD_STRATEGIES:
                    raise ValueError(
                        f"Bead {bead_id} of {residue} has an unknown strategy "
                        f"'{strategy}'. Use one of: {', '.join(BEAD_STRATEGIES)}."
                    )

        # The coarse-graining connects these beads in every residue it keeps.
        connections = [
            (f"Connection {first}–{second}", (first, second))
            for first, second in self.connectivity.intra_residue
        ] + [
            (
                f"Inter-residue connection {link.source} → {link.target}",
                (link.source, link.target),
            )
            for link in self.connectivity.inter_residue
        ]
        for label, ends in connections:
            for bead_id in dict.fromkeys(ends):
                missing = [
                    residue
                    for residue, beads in residue_beads.items()
                    if bead_id not in beads
                ]
                if missing:
                    raise ValueError(
                        f"{label}: bead {bead_id} is not defined for {', '.join(missing)}."
                    )
        return self

    def _resolve_residue_configs(self) -> dict[str, dict[str, dict]]:
        """Apply the mapping overrides as the coarse-graining model does."""
        default_residues = self.default_mapping.residues
        configs = {
            residue: self.default_mapping.config.model_dump()
            for residue in default_residues
        }
        for entry in self.mapping:
            for residue in entry.residues:
                if residue not in configs:
                    raise ValueError(
                        f"Residue {residue} has a mapping but is not listed in "
                        "default_mapping residues."
                    )
                for section, values in entry.config.model_dump().items():
                    configs[residue][section].update(values)
        return configs

    def _resolve_residue_beads(self) -> dict[str, set[str]]:
        return {
            residue: set(config["bead_names"])
            for residue, config in self._resolve_residue_configs().items()
        }
