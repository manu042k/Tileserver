import os
from pathlib import Path

# Make TIFF file path configurable via environment variable
DEFAULT_TIFF_PATH = Path(__file__).parent / "TIFF-Storrage" / "snowdepth.tiff"
TIFF_FILE = os.environ.get("TIFF_FILE_PATH", str(DEFAULT_TIFF_PATH))
