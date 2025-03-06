"""
Middleware components for the Tile Server application.
"""
import time
from fastapi import Request
from logger import setup_logger

# Setup logger for this module
logger = setup_logger('middleware')

async def log_requests(request: Request, call_next):
    """
    Middleware that logs information about HTTP requests and responses.
    
    Args:
        request: The incoming request
        call_next: Function to process the request
        
    Returns:
        The response from the next middleware or route handler
    """
    start_time = time.time()
    
    # Get client IP and requested path
    client_host = request.client.host if request.client else "unknown"
    path = request.url.path
    
    logger.info(f"Request started: {request.method} {path} from {client_host}")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate and log processing time
    process_time = time.time() - start_time
    logger.info(f"Request completed: {request.method} {path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    return response
