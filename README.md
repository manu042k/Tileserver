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
