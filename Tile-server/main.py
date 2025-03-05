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

app = FastAPI(title="GeoTIFF Tile Server")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "server": "GeoTIFF Tile Server",
        "endpoints": {
            "tiles": "/tiles/{z}/{x}/{y}.png",
            "health": "/health"
        },
        "tiff_file": TIFF_FILE,
        "tiff_exists": Path(TIFF_FILE).exists()
    }

@app.get("/tiles/{z}/{x}/{y}.png")
async def get_tile(z: int, x: int, y: int):
    """Generate and serve a tile from the GeoTIFF file with original colors preserved."""
    tile_bytes, error = TileService.generate_tile(z, x, y)
    
    if error:
        raise HTTPException(status_code=500, detail=error)
        
    return Response(content=tile_bytes, media_type="image/png")

@app.get("/health")
async def health_check():
    """Health check endpoint that also verifies TIFF file availability."""
    if Path(TIFF_FILE).exists():
        return {"status": "healthy", "tiff_file": TIFF_FILE, "tiff_exists": True}
    else:
        return {"status": "unhealthy", "tiff_file": TIFF_FILE, "tiff_exists": False}

if __name__ == "__main__":
    # Validate TIFF file on startup
    if not validate_tiff_file():
        print("Warning: Starting server without valid TIFF file. Some endpoints may not work correctly.")
    else:
        print(f"TIFF file found at: {TIFF_FILE}")
    
    print("Starting tile server at http://localhost:8000")
    print("Try accessing:")
    print("  - Health check: http://localhost:8000/health")
    print("  - Sample tile: http://localhost:8000/tiles/5/10/10.png")
    
    # Update to use local path
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
