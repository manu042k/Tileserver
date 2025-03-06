"""
Main module for the GeoTIFF Tile Server.
"""
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import sys

# Add the parent directory to path to enable imports
sys.path.append(str(Path(__file__).parent.parent))

# Use direct imports instead of package imports
from config import TIFF_FILE
from utils import validate_tiff_file
from tile_service import TileService
from logger import setup_logger
from middleware import log_requests

# Setup logger for this module
logger = setup_logger('main')


app = FastAPI(title="GeoTIFF Tile Server")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for request logging
app.middleware("http")(log_requests)

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting GeoTIFF Tile Server")
    
    # Validate TIFF file on startup
    if not validate_tiff_file():
        logger.warning("Starting server without valid TIFF file. Some endpoints may not work correctly.")
    else:
        logger.info(f"TIFF file found at: {TIFF_FILE}")

@app.get("/")
async def root():
    """Root endpoint with server information."""
    tiff_exists = Path(TIFF_FILE).exists()
    logger.info(f"Root endpoint accessed, TIFF file exists: {tiff_exists}")
    
    return {
        "server": "GeoTIFF Tile Server",
        "endpoints": {
            "tiles": "/tiles/{z}/{x}/{y}.png",
            "health": "/health"
        },
        "tiff_file": TIFF_FILE,
        "tiff_exists": tiff_exists
    }

@app.get("/tiles/{z}/{x}/{y}.png")
async def get_tile(z: int, x: int, y: int):
    """Generate and serve a tile from the GeoTIFF file with original colors preserved."""
    logger.info(f"Tile requested: z={z}, x={x}, y={y}")
    
    tile_bytes, error = TileService.generate_tile(z, x, y)
    
    if error:
        logger.error(f"Error generating tile z={z}, x={x}, y={y}: {error}")
        raise HTTPException(status_code=500, detail=error)
    
    logger.debug(f"Serving tile: z={z}, x={x}, y={y}")    
    return Response(content=tile_bytes, media_type="image/png")

@app.get("/health")
async def health_check():
    """Health check endpoint that also verifies TIFF file availability."""
    tiff_exists = Path(TIFF_FILE).exists()
    logger.info(f"Health check: TIFF file exists: {tiff_exists}")
    
    if tiff_exists:
        return {"status": "healthy", "tiff_file": TIFF_FILE, "tiff_exists": True}
    else:
        return {"status": "unhealthy", "tiff_file": TIFF_FILE, "tiff_exists": False}

if __name__ == "__main__":
    # Validate TIFF file on startup
    if not validate_tiff_file():
        logger.warning("Starting server without valid TIFF file. Some endpoints may not work correctly.")
    else:
        logger.info(f"TIFF file found at: {TIFF_FILE}")
    
    logger.info("Starting tile server at http://localhost:8000")
    logger.info("Try accessing:")
    logger.info("  - Health check: http://localhost:8000/health")
    logger.info("  - Sample tile: http://localhost:8000/tiles/5/10/10.png")
    
    # Run the app directly
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
