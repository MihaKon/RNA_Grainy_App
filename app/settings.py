import pathlib

from fastapi.templating import Jinja2Templates

BASE_DIR = pathlib.Path(__file__).resolve().parent
COARSE_GRAIN_MODELS_DIR = BASE_DIR / "coarse_grain" / "models"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
TEMP_DIR = BASE_DIR.parent / "temp"
TEMPLATES = Jinja2Templates(directory=TEMPLATES_DIR)

MODELS_IMAGES_DIR = STATIC_DIR / "images"
EXAMPLES_DIR = STATIC_DIR / "examples"
CITATIONS_DIR = BASE_DIR / "coarse_grain" / "metadata" / "citations.json"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_UPLOAD_SIZE = 25 * 1024 * 1024
MAX_RCSB_UPLOAD_SIZE = 25 * 1024 * 1024
