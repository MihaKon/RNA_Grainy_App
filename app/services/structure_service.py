from collections import defaultdict
from io import StringIO
from typing import Any, DefaultDict

from Bio.PDB.Structure import Structure
from Bio.PDB.StructureBuilder import StructureBuilder

from app.coarse_grain.parser import CoarseGrainModels, transform_to_coarse_grain
from app.models import SupportedFormats
from app.validators import count_structure_entities, get_format_parser


class StructureProcessor:
    @staticmethod
    def parse_structure(
        content: str, filename: str, file_format: SupportedFormats
    ) -> Structure:
        file_like = StringIO(content)
        parser: StructureBuilder = get_format_parser(file_format)
        return parser.get_structure(filename, file_like)  # type: ignore

    @staticmethod
    def apply_coarse_graining(structure: Structure, model: CoarseGrainModels) -> str:
        coarse_file = transform_to_coarse_grain(structure, model)
        return coarse_file.getvalue()

    @staticmethod
    def build_comparison_context(
        filename: str,
        original_content: str,
        coarse_content: str,
        file_format: str,
        selected_model: str,
        original_structure: Structure,
        coarse_structure: Structure,
    ) -> DefaultDict[str, Any]:
        display_format = "mmcif" if file_format == SupportedFormats.CIF else file_format

        initial_data = {
            "filename": filename,
            "file_format": [display_format, SupportedFormats.PDB.value],
            "file_data": [original_content, coarse_content],
            "selected_model": selected_model,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)

        for structure in [original_structure, coarse_structure]:
            counts = count_structure_entities(structure)
            for key, count in counts.items():
                context[key].append(count)

        return context
