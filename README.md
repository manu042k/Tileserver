# Slippy Map Server - Snowmap Interview Assignment

Being a developer at a startup means venturing into the unknown and learning quickly. This assessment is designed to evaluate your problem-solving skills when tackling an unfamiliar challenge.

## Overview

In this assessment, you will implement a simple service to extract map tiles from a geospatial raster dataset and serve them as PNG images. Tiles are generated based on coordinates (`x, y, z`)—representing horizontal index, vertical index, and zoom level, respectively. Your solution will process a provided GeoTIFF file and return 256x256 PNG tiles via a local web server. You may use any programming language of your choice.

### References

- [Tiled Web Maps (Wiki)](https://en.wikipedia.org/wiki/Tiled_web_map)
- [Slippy Map Tile Naming (OpenStreetMap)](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)

### Provided Resources

- A TIFF file as the source for tile generation: `snowdepth.tiff`
- A Mapbox implementation in `mapbox/src/App.js` with a Snowmap tile server

### Objective

1. Create a web service that extracts tiles from `snowdepth.tiff` based on tile coordinates (`x, y, z`)
2. Serve the tiles as PNG images over HTTP
3. Run the service on localhost - no deployment is required
4. Replace the tile layer in `App.js` with your own implementation

### Expectations

- Your implementation supports dynamic image generation - meaning it works with any given TIFF file.
- You are encouraged to use any tools, libraries, or frameworks that help achieve the goal. Make sure you include references.
- The final solution should be well-structured and documented.
- You DO NOT need to deploy the server; running it on `localhost` is sufficient.

## Getting Started with the Environment

To set up the Mapbox environment we have provided, run the following commands:

```bash
cd mapbox
npm install
npm start
```

Once the setup completes successfully, a map should appear in your browser.

Your task is to replace the server that provides tiles on the map with your own localhost server URL.

## Deliverables

### Code Submission:

- Push your implementation to a public GitHub repository.
- Update this `README.md` with setup and usage instructions.

### Demo Video:

- Record a short video (screen recording) demonstrating your server in action.
- Upload it to a platform like YouTube (unlisted) or Google Drive and share the link.

### Submit your work:

- Email the GitHub repository link along with the demo video link.

## Candidate Submission

### Setup & Usage

**Prerequisites**

- Docker
- GeoTIFF file

**Installation**

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   ```

2. **Add your GeoTIFF file**

   ```bash
   cd Tile-server/TIFF-Storage
   ```

   Add your TIFF file here.

3. **Edit Config file**

   ```bash
   cd Tile-server/config.py
   ```

   Change `TIFF_Name` to your file name:

   ```python
   TIFF_Name = "snowdepth.tiff"
   ```

4. **Build and run with Docker Compose**

   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Mapbox viewer: http://localhost:3000
   - Tile server API: http://localhost:8000
   - Direct tile access: http://localhost:8000/tiles/{z}/{x}/{y}.png
   - API documentation: http://localhost:8000/docs#/

### Tile Server

The tile server is built with Python and provides the following functionality:

1. **Tile Generation**: Extracts 256x256 pixel PNG tiles from the GeoTIFF based on coordinates (x, y, z)
2. **Coordinate Transformation**: Converts between tile coordinates and geographic coordinates
3. **Resampling**: Applies appropriate resampling methods based on zoom level
4. **Special Handling**: Provides optimizations for low zoom levels and polar regions

#### Key Components

- **TileService**: Core service for generating tiles from GeoTIFF data
- **FastAPI Server**: REST API for serving tiles over HTTP
- **Coordinate Utils**: Functions for tile mathematics and coordinate transformations

#### Technical Details

1. **Coordinate Systems**:

   - Web Mercator (EPSG:3857) for tile output
   - WGS84 (EPSG:4326) for geographic calculations

2. **Resampling Methods**:

   - High zoom (≥14): Cubic resampling for detailed views
   - Medium zoom (8-13): Bilinear resampling for balanced quality
   - Low zoom (<8): Average resampling for overview perspectives

3. **Optimizations**:
   - Contrast adjustment for polar regions
   - Alternative rendering for very low zoom levels
   - Empty tile detection for areas outside source data
   - Proper handling of no-data values

### Tech Stack Used:

- **FastAPI**: Provides asynchronous support for building web APIs
- **Rasterio**: Handles geospatial raster data processing
- **Docker**: Facilitates containerization for consistent environments
- **Clean Architecture**: Ensures a maintainable and scalable codebase

### Video demo:

- [Youtube Link](https://youtu.be/ozhviQ5lWVY)

### Acknowledgement

- Utilized AI tools solely for understanding concepts and optimization
