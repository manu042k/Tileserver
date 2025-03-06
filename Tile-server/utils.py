import math
from pathlib import Path
import os
from config import TIFF_FILE
from logger import setup_logger

# Setup logger for this module
logger = setup_logger('utils')

def validate_tiff_file():
    """Validate that the TIFF file exists and is accessible."""
    tiff_path = Path(TIFF_FILE)
    if not tiff_path.exists():
        logger.error(f"TIFF file not found at path: {TIFF_FILE}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info("Please ensure the file exists or set the correct path using the TIFF_FILE_PATH environment variable")
        tiff_path.parent.mkdir(parents=True, exist_ok=True)
        return False
    logger.info(f"TIFF file validated at path: {TIFF_FILE}")
    return True

def tile_bounds(x, y, z):
    """Convert tile coordinates (x, y, z) to geospatial bounds."""
    n = 2.0 ** z
    lon_left = x / n * 360.0 - 180.0
    lon_right = (x + 1) / n * 360.0 - 180.0
    lat_top = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_bottom = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon_left, lat_bottom, lon_right, lat_top

def create_empty_tile():
    """Create an empty transparent tile and return its bytes."""
    from PIL import Image
    import io
    
    logger.debug("Creating empty transparent tile")
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes.getvalue()
