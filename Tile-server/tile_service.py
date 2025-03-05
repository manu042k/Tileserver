import io
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from PIL import Image
import traceback
from pathlib import Path

# Use direct imports instead of package imports
from utils import tile_bounds, create_empty_tile
from config import TIFF_FILE

class TileService:
    """Service for processing and generating map tiles from GeoTIFF data."""
    
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
        if not Path(TIFF_FILE).exists():
            return None, f"TIFF file not found at path: {TIFF_FILE}. Please check the server configuration."
            
        try:
            with rasterio.open(TIFF_FILE) as src:
                # Get the bounds of the requested tile
                lon_west, lat_south, lon_east, lat_north = tile_bounds(x, y, z)
                
                # Create a target image with the right dimensions
                width, height = 256, 256
                
                # Define the transformation for this tile
                dst_transform = rasterio.transform.from_bounds(
                    lon_west, lat_south, lon_east, lat_north, width, height
                )
                
                # Get the number of bands from the source
                band_count = src.count
                
                # Create arrays for our target data - one for each band
                dst_shape = (band_count, height, width)
                dst_data = np.zeros(dst_shape, dtype=rasterio.float32)
                
                try:
                    # Reproject the data from the source to our tile
                    reproject(
                        source=rasterio.band(src, range(1, band_count + 1)),
                        destination=dst_data,
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=dst_transform,
                        dst_crs=src.crs,
                        resampling=Resampling.bilinear
                    )
                except Exception:
                    # If reprojection fails, return an empty tile
                    return create_empty_tile(), None
                
                # Handle nodata values
                if hasattr(src, 'nodata') and src.nodata is not None:
                    for i in range(band_count):
                        mask = dst_data[i] == src.nodata
                        dst_data[i] = np.ma.array(dst_data[i], mask=mask)
                
                # Check for empty data
                if np.all(np.isnan(dst_data)) or dst_data.size == 0:
                    return create_empty_tile(), None
                
                # Clean data: Replace NaNs and infinities
                dst_data = np.nan_to_num(dst_data)
                
                # Process based on band count and create the appropriate image
                img = TileService._process_bands(src, dst_data, band_count, height, width)
                
                # Save to PNG
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                
                return img_bytes.getvalue(), None
        
        except Exception as e:
            error_details = f"Error: {str(e)}\n{traceback.format_exc()}"
            print(error_details)
            return None, str(e)
    
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
        if src.colormap(1):
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
