import os
import pathlib

from fastapi.templating import Jinja2Templates

# Application
APP_VERSION = os.getenv("APP_VERSION", "dev").removeprefix("v")


# Unit conversions
BYTES_PER_KIB = 1024
BYTES_PER_MIB = 1024**2
BYTES_PER_GIB = 1024**3

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE


# Paths
BASE_DIR = pathlib.Path(__file__).resolve().parent

COARSE_GRAIN_MODELS_DIR = BASE_DIR / "coarse_grain" / "models"
CITATIONS_DIR = BASE_DIR / "coarse_grain" / "metadata" / "citations.json"

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
MODELS_IMAGES_DIR = STATIC_DIR / "images"
PRESETS_DIR = STATIC_DIR / "presets"

WORKSPACE_STORAGE_DIR = BASE_DIR.parent / "temp"


# Structure files
PDB_MAX_ATOM_COUNT = 99999


# Uploads and RCSB downloads
RCSB_URL = "https://files.rcsb.org/download/"

MAX_FILE_UPLOAD_SIZE = 100 * BYTES_PER_MIB
MAX_RCSB_DOWNLOAD_SIZE = 100 * BYTES_PER_MIB

ALLOWED_PRESET_IDS = {"1EHZ", "1MNX", "2F8S"}


# Custom model input limits
JSON_MAX_CHARS = 5000
JSON_MAX_UPLOAD_SIZE = 8 * BYTES_PER_KIB


# Temporary workspace storage
WORKSPACE_MAX_LIFETIME = 24 * SECONDS_PER_HOUR
WORKSPACE_CLEANUP_INTERVAL = 15 * SECONDS_PER_MINUTE
WORKSPACE_STORAGE_MAX_SIZE = 4 * BYTES_PER_GIB
MIN_FREE_DISK_SIZE = 2 * BYTES_PER_GIB


# Initialization
TEMPLATES = Jinja2Templates(directory=TEMPLATES_DIR)
WORKSPACE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
