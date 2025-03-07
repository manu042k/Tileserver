"""
This module is used to configure the tile server. It reads the TIFF file path from the environment variable
TIFF_FILE_PATH, or uses a default path if the environment variable is not set.
"""
import os
from pathlib import Path
from logger import setup_logger

# Setup logger for this module
logger = setup_logger('config')

TIFF_Name = "snowdepth.tiff"       #Edit this to change the name of the tiff file

# Make TIFF file path configurable via environment variable

DEFAULT_TIFF_PATH = Path(__file__).parent / "TIFF-Storrage" / TIFF_Name
TIFF_FILE = os.environ.get("TIFF_FILE_PATH", str(DEFAULT_TIFF_PATH))

logger.info(f"Using TIFF file path: {TIFF_FILE}")
if "TIFF_FILE_PATH" in os.environ:
    logger.debug("TIFF file path set from environment variable")
else:
    logger.debug("Using default TIFF file path")
