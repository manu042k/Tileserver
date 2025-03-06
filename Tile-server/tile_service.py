import io
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.crs import CRS
from PIL import Image
import traceback
from pathlib import Path
from utils import tile_bounds, create_empty_tile
from config import TIFF_FILE
from logger import setup_logger

# Setup logger for this module
logger = setup_logger('tile_service')

class TileService:
    """Service for processing and generating map tiles from GeoTIFF data."""
    
    # Define standard projections
    WEB_MERCATOR = CRS.from_epsg(3857)
    WGS84 = CRS.from_epsg(4326)
    
    @staticmethod
    def generate_tile(z: int, x: int, y: int):
        """
        Generate a tile from the GeoTIFF file with original colors preserved.
        
        Args:
            z: Zoom level
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tuple of (tile_bytes, error_message)
            If successful, error_message will be None
            If error occurs, tile_bytes will be None and error_message will contain the error
        """
        logger.info(f"Generating tile with coordinates z={z}, x={x}, y={y}")
        
        if not Path(TIFF_FILE).exists():
            error_msg = f"TIFF file not found at path: {TIFF_FILE}. Please check the server configuration."
            logger.error(error_msg)
            return None, error_msg
            
        try:
            logger.debug(f"Opening TIFF file: {TIFF_FILE}")
            with rasterio.open(TIFF_FILE) as src:
                # Get the bounds of the requested tile in WGS84
                lon_west, lat_south, lon_east, lat_north = tile_bounds(x, y, z)
                logger.debug(f"Tile bounds (WGS84): {lon_west}, {lat_south}, {lon_east}, {lat_north}")
                
                # Determine the source CRS - assume WGS84 if none is specified
                src_crs = src.crs if src.crs else TileService.WGS84
                logger.debug(f"Source CRS: {src_crs}")
                
                # Convert tile bounds to Web Mercator for proper display
                west, south, east, north = transform_bounds(
                    TileService.WGS84,  # Input is in WGS84 from tile_bounds
                    TileService.WEB_MERCATOR,  # Output in Web Mercator
                    lon_west, lat_south, lon_east, lat_north
                )
                
                # Create a target image with the right dimensions
                width, height = 256, 256
                
                # Define the transformation for this tile in Web Mercator
                dst_transform = rasterio.transform.from_bounds(
                    west, south, east, north, width, height
                )
                
                # Get the number of bands from the source
                band_count = src.count
                logger.debug(f"Source has {band_count} bands")
                
                # Create arrays for our target data - one for each band
                dst_shape = (band_count, height, width)
                dst_data = np.zeros(dst_shape, dtype=rasterio.float32)
                
                # Select resampling method based on zoom level
                resampling_method = TileService._get_resampling_for_zoom(z)
                logger.debug(f"Using resampling method: {resampling_method}")
                
                try:
                    # Reproject the data from the source CRS to Web Mercator
                    logger.debug("Reprojecting data...")
                    reproject(
                        source=rasterio.band(src, range(1, band_count + 1)),
                        destination=dst_data,
                        src_transform=src.transform,
                        src_crs=src_crs,
                        dst_transform=dst_transform,
                        dst_crs=TileService.WEB_MERCATOR,  # Always use Web Mercator for output
                        resampling=resampling_method
                    )
                except Exception as e:
                    logger.warning(f"Reprojection error: {e}")
                    logger.debug(f"Tile coordinates: z={z}, x={x}, y={y}")
                    logger.debug(f"Source CRS: {src_crs}")
                    logger.debug(f"Bounds (WGS84): {lon_west}, {lat_south}, {lon_east}, {lat_north}")
                    
                    # Try alternative approach for low zoom levels where standard reprojection might fail
                    if z < 5:
                        logger.info(f"Attempting alternative low-zoom rendering for z={z}")
                        return TileService._generate_low_zoom_tile(src, z, x, y, src_crs)
                    else:
                        # If reprojection fails, return an empty tile
                        logger.warning("Reprojection failed, returning empty tile")
                        return create_empty_tile(), None
                
                # Handle nodata values
                if hasattr(src, 'nodata') and src.nodata is not None:
                    logger.debug(f"Handling nodata values: {src.nodata}")
                    for i in range(band_count):
                        mask = dst_data[i] == src.nodata
                        dst_data[i] = np.ma.array(dst_data[i], mask=mask)
                
                # Check for empty data
                if np.all(np.isnan(dst_data)) or dst_data.size == 0:
                    logger.debug("Empty data detected, returning empty tile")
                    return create_empty_tile(), None
                
                # Clean data: Replace NaNs and infinities
                logger.debug("Cleaning data (replace NaNs and infinities)")
                dst_data = np.nan_to_num(dst_data)
                
                # Special handling for low zoom levels to reduce distortion
                if z < 5:
                    logger.debug(f"Applying low-zoom adjustments for z={z}")
                    dst_data = TileService._adjust_for_low_zoom(dst_data, z, lat_south, lat_north)
                
                # Process based on band count and create the appropriate image
                logger.debug(f"Processing {band_count} bands to create image")
                img = TileService._process_bands(src, dst_data, band_count, height, width)
                
                # Save to PNG
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                
                logger.info(f"Successfully generated tile z={z}, x={x}, y={y}")
                return img_bytes.getvalue(), None
        
        except Exception as e:
            error_details = f"Error generating tile: {str(e)}"
            logger.error(error_details)
            logger.debug(traceback.format_exc())
            return None, str(e)
    
    @staticmethod
    def _get_resampling_for_zoom(zoom_level):
        """Select appropriate resampling algorithm based on zoom level."""
        if zoom_level >= 14:
            return Resampling.cubic  # Higher quality for detailed views
        elif zoom_level >= 8:
            return Resampling.bilinear  # Good balance for mid-range zoom
        else:
            return Resampling.average  # Better for overview/zoomed-out views
    
    @staticmethod
    def _adjust_for_low_zoom(data, zoom_level, lat_south, lat_north):
        """
        Apply corrections to reduce distortion at low zoom levels.
        This is especially important for areas far from the equator.
        """
        # Only apply corrections at low zoom levels
        if zoom_level >= 5:
            return data
            
        # Calculate latitude factor - distortion increases with distance from equator
        # Calculate average latitude of the tile
        avg_lat = (lat_north + lat_south) / 2.0
        # Factor increases as we get further from equator
        lat_factor = abs(avg_lat) / 90.0  # 0 at equator, 1 at poles
        
        # For very low zoom levels, reduce contrast based on latitude
        # This helps prevent extreme stretching in polar regions
        if zoom_level <= 2:
            # More aggressive correction for very low zoom
            blend_factor = 0.6 - (0.3 * lat_factor)
        else:
            # Milder correction for zoom 3-4
            blend_factor = 0.8 - (0.2 * lat_factor)
            
        # Apply the blend - move values closer to their mean to reduce contrast
        for i in range(data.shape[0]):
            band_mean = np.mean(data[i])
            data[i] = data[i] * blend_factor + band_mean * (1 - blend_factor)
            
        return data
    
    @staticmethod
    def _generate_low_zoom_tile(src, z, x, y, src_crs):
        """
        Alternative tile generation method for very low zoom levels.
        Uses simplified rendering to avoid extreme distortion.
        """
        logger.info(f"Using low-zoom tile generation for z={z}, x={x}, y={y}")
        try:
            # Get tile bounds in WGS84
            lon_west, lat_south, lon_east, lat_north = tile_bounds(x, y, z)
            logger.debug(f"Low-zoom tile bounds (WGS84): {lon_west}, {lat_south}, {lon_east}, {lat_north}")
            
            # Target dimensions
            width, height = 256, 256
            
            # Get source bounds in WGS84 for comparison
            src_bounds_wgs84 = src.bounds
            if src_crs != TileService.WGS84:
                src_bounds_wgs84 = transform_bounds(
                    src_crs, TileService.WGS84, *src.bounds
                )
            
            # Check for overlap between tile and source
            if (lon_east < src_bounds_wgs84[0] or lon_west > src_bounds_wgs84[2] or 
                lat_north < src_bounds_wgs84[1] or lat_south > src_bounds_wgs84[3]):
                logger.debug("Tile doesn't overlap with source data, returning empty tile")
                return create_empty_tile(), None
                
            # For very low zoom, create a simpler representation
            band_count = src.count
            logger.debug(f"Creating simplified tile with {band_count} bands")
            
            if band_count == 1:
                # For single-band rasters, create a grayscale image
                img_data = np.zeros((height, width), dtype=np.uint8)
                
                # Read a downsampled version of the source data
                overview_level = min(z, src.overviews(1) or [0])
                logger.debug(f"Using overview level: {overview_level}")
                source_data = src.read(1, out_shape=(1, height, width), resampling=Resampling.average)
                
                # Normalize to 0-255 range
                if source_data.size > 0:
                    min_val = np.min(source_data)
                    max_val = np.max(source_data)
                    logger.debug(f"Source data range: {min_val} to {max_val}")
                    if max_val > min_val:
                        img_data = np.clip(
                            ((source_data - min_val) / (max_val - min_val) * 255).astype(np.uint8),
                            0, 255
                        )
                
                # Create image from the data
                img = Image.fromarray(img_data, mode='L')
            else:
                # For multi-band rasters, create an RGB image
                img_data = np.zeros((height, width, min(3, band_count)), dtype=np.uint8)
                
                # Process up to 3 bands (RGB)
                for i in range(min(3, band_count)):
                    source_data = src.read(i+1, out_shape=(1, height, width), resampling=Resampling.average)
                    
                    if source_data.size > 0:
                        min_val = np.min(source_data)
                        max_val = np.max(source_data)
                        logger.debug(f"Band {i+1} data range: {min_val} to {max_val}")
                        if max_val > min_val:
                            img_data[:, :, i] = np.clip(
                                ((source_data - min_val) / (max_val - min_val) * 255).astype(np.uint8),
                                0, 255
                            )
                
                # Create image from the data
                img = Image.fromarray(img_data, mode='RGB' if band_count >= 3 else 'L')
            
            # Save to PNG
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            logger.info(f"Successfully generated low-zoom tile z={z}, x={x}, y={y}")
            return img_bytes.getvalue(), None
        
        except Exception as e:
            error_msg = f"Error generating low zoom tile: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return create_empty_tile(), None
    
    @staticmethod
    def _process_bands(src, dst_data, band_count, height, width):
        """Process bands based on count and create appropriate image."""
        if band_count == 1:
            return TileService._process_single_band(src, dst_data, height, width)
        elif band_count == 3:
            return TileService._process_rgb_bands(dst_data, height, width)
        elif band_count == 4:
            return TileService._process_rgba_bands(dst_data, height, width)
        else:
            return TileService._process_multiband(dst_data, band_count, height, width)
    
    @staticmethod
    def _process_single_band(src, dst_data, height, width):
        """Process a single band image, applying colormap if available."""
        if hasattr(src, 'colormap') and src.colormap(1):
            # Use the colormap
            colormap = src.colormap(1)
            rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Scale data to the range of colormap indices
            min_val = np.min(dst_data[0])
            max_val = np.max(dst_data[0])
            if max_val > min_val:
                scaled_data = np.clip(
                    ((dst_data[0] - min_val) / (max_val - min_val) * 255).astype(np.uint8),
                    0, 255
                )
            else:
                scaled_data = np.zeros((height, width), dtype=np.uint8)
            
            # Apply colormap
            for i in range(height):
                for j in range(width):
                    pixel_value = scaled_data[i, j]
                    if pixel_value in colormap:
                        rgb_data[i, j] = [colormap[pixel_value][0], 
                                        colormap[pixel_value][1], 
                                        colormap[pixel_value][2]]
            
            return Image.fromarray(rgb_data, mode='RGB')
        else:
            # No colormap, create a grayscale image
            min_val = np.min(dst_data[0])
            max_val = np.max(dst_data[0])
            if max_val > min_val:
                img_data = np.clip(
                    ((dst_data[0] - min_val) / (max_val - min_val) * 255).astype(np.uint8),
                    0, 255
                )
            else:
                img_data = np.zeros((height, width), dtype=np.uint8)
            
            return Image.fromarray(img_data, mode='L')
    
    @staticmethod
    def _process_rgb_bands(dst_data, height, width):
        """Process RGB (3-band) image data."""
        rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(3):
            min_val = np.min(dst_data[i])
            max_val = np.max(dst_data[i])
            if max_val > min_val:
                rgb_data[:, :, i] = np.clip(
                    ((dst_data[i] - min_val) / (max_val - min_val) * 255).astype(np.uint8),
                    0, 255
                )
        
        return Image.fromarray(rgb_data, mode='RGB')
    
    @staticmethod
    def _process_rgba_bands(dst_data, height, width):
        """Process RGBA (4-band) image data."""
        rgba_data = np.zeros((height, width, 4), dtype=np.uint8)
        for i in range(4):
            min_val = np.min(dst_data[i])
            max_val = np.max(dst_data[i])
            if max_val > min_val:
                rgba_data[:, :, i] = np.clip(
                    ((dst_data[i] - min_val) / (max_val - min_val) * 255).astype(np.uint8),
                    0, 255
                )
        
        return Image.fromarray(rgba_data, mode='RGBA')
    
    @staticmethod
    def _process_multiband(dst_data, band_count, height, width):
        """Process multi-band data using the first three bands as RGB."""
        rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(min(3, band_count)):
            min_val = np.min(dst_data[i])
            max_val = np.max(dst_data[i])
            if max_val > min_val:
                rgb_data[:, :, i] = np.clip(
                    ((dst_data[i] - min_val) / (max_val - min_val) * 255).astype(np.uint8),
                    0, 255
                )
        
        return Image.fromarray(rgb_data, mode='RGB')
