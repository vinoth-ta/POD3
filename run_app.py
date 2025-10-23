#!/usr/bin/env python3
"""
Main entry point for STTM-to-Notebook Generator API
Runs the application with Swagger UI enabled
"""

import uvicorn
import sys
from pathlib import Path

# Add the project root to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Import the FastAPI app
from sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator import app

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Starting STTM-to-Notebook Generator API v1.1.0")
    print("=" * 80)
    print(f"📂 Project Root: {BASE_DIR}")
    print(f"📋 Swagger UI: http://localhost:8000/docs")
    print(f"📋 ReDoc: http://localhost:8000/redoc")
    print(f"📋 OpenAPI JSON: http://localhost:8000/openapi.json")
    print("=" * 80)
    
    # Run the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

