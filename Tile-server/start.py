"""
Script to start the Tile Server properly.
This avoids import issues by running the app as a module.
"""
import uvicorn
import os

# Change into the same directory as the script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

if __name__ == "__main__":
    print("Starting tile server at http://localhost:8000")
    print("Try accessing:")
    print("  - Health check: http://localhost:8000/health")
    print("  - Sample tile: http://localhost:8000/tiles/5/10/10.png")
    
    # Run the app using the module path
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
