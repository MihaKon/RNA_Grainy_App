import json
from enum import Enum
from typing import Any

from app.settings import COARSE_GRAIN_MODELS_DIR


class CoarseGrainModels(Enum):
    DUMMY = "simrna.json"

    def model(self) -> dict[str, Any]:
        with open(COARSE_GRAIN_MODELS_DIR / self.value) as f:
            result = json.load(f)
        return result
