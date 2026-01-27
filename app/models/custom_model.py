from pydantic import BaseModel, ConfigDict, field_validator

strict_config = ConfigDict(extra="forbid")


class MappingConfig(BaseModel):
    model_config = strict_config
    bead_names: dict[str, str]
    atom_centers: dict[str, list[str]]
    description: dict[str, str]
    strategies: dict[str, str]


class MappingEntry(BaseModel):
    model_config = strict_config
    residues: list[str]
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
    default_mapping: MappingEntry | None = None
    mapping: list[MappingEntry] = []
    connectivity: Connectivity | None = None
