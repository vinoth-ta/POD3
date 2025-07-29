#!/usr/bin/env python3
"""
Parallel Server Runner for STTM to Notebook Generator API
Runs both V1.0.0 and V1.1.0 versions simultaneously on different ports.
"""

import subprocess
import time
import signal
import sys
import os
import threading
from pathlib import Path

class ParallelServerRunner:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def create_v1_app(self):
        """Create V1.0.0 FastAPI app dynamically"""
        v1_app_code = '''
from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from typing import List
import json
from sttm_to_notebook_generator_integrated.read_env_var import *

async def get_client_ip(request: Request):
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host
    return ip

# Import the OLD VERSION (V1.0.0)
from sttm_to_notebook_generator_integrated.api1_json_converter import app1 as json_converter_router_v1
from notebook_generator_app.main import app2 as notebook_generator_router
from notebook_generator_app.schemas.models import PromptRequestModel, PromptResponseModel, MetaInfo
from sttm_to_notebook_generator_integrated.log_handler import get_logger
logger = get_logger("<API3 :: V1.0.0 Encapsulator>")

# Initialize the V1.0.0 FastAPI application
app_v1 = FastAPI(
    title="STTM to Notebook Generation API - V1.0.0",
    description="Original version of the STTM to Notebook Generation API.",
    version="1.0.0"
)

# Include the routers
app_v1.include_router(json_converter_router_v1)
app_v1.include_router(notebook_generator_router)

appName = os.environ.get('rootContext')

# Define the V1.0.0 endpoint
@app_v1.post(f"/{appName}/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook",
          summary="V1.0.0: Full Process: Convert STTM to JSON and Generate Silver Notebook",
          response_model=PromptResponseModel,
          response_description="The path to the generated ETL Notebook and status.",
          responses={
              400: {"description": "Bad Request - Invalid input"},
              422: {"description": "Validation Error - Schema mismatch"},
              500: {"description": "Internal Server Error"}
          })
async def full_process_generate_notebook_v1(
    request: Request,
    sttm_metadata_json: str = Form(..., description="JSON string of a list of dictionaries containing STTM metadata."),
    sttm_files: List[UploadFile] = File(..., description="List of STTM Excel files to be processed."),
    notebook_metadata_json: str = Form(..., description="JSON string containing metadata for the notebook generation.")
):
    """
    V1.0.0: This endpoint orchestrates the entire process using the original implementation.
    """
    client_ip = await get_client_ip(request)
    logger.info(f"V1.0.0 Request received from IP: {client_ip}")
    
    try:
        # Import the OLD VERSION function
        from sttm_to_notebook_generator_integrated.api1_json_converter import orchestrate_json_sttm as process_sttm_to_json_v1

        # Execute the V1.0.0 logic
        json_conversion_output = await process_sttm_to_json_v1(
            sttm_metadata_json=sttm_metadata_json,
            sttm_files=sttm_files,
            notebook_metadata_json=notebook_metadata_json
        )
        
        logger.debug(f"V1.0.0 JSON conversion output: {json_conversion_output}")
        
        # Process the output for notebook generation (same logic as V1.1.0)
        processed_notebook_meta = json_conversion_output["notebook_metadata_json"]
        
        # Create the request model for notebook generation
        prompt_request = PromptRequestModel(
            status_code=json_conversion_output["status_code"],
            notebook_metadata_json=MetaInfo(**processed_notebook_meta),
            content=json_conversion_output["content"]
        )
        
        # Call the notebook generation endpoint
        from notebook_generator_app.main import generate_response
        notebook_response = await generate_response(prompt_request)
        
        logger.info("V1.0.0: Notebook generation completed successfully!")
        return notebook_response
        
    except Exception as e:
        logger.error(f"V1.0.0 Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"V1.0.0 Processing failed: {str(e)}")

@app_v1.get(f"/{appName}/v1")
async def read_root_v1():
    return {"message": "STTM to Notebook Generation API - V1.0.0", "version": "1.0.0"}

@app_v1.get(f"/{appName}/v1/health")
async def health_check_v1():
    return {"status": "healthy", "version": "1.0.0"}
'''
        
        # Write V1.0.0 app to a temporary file
        v1_app_path = Path("sttm_to_notebook_generator_integrated/api3_sttm_to_notebook_generator_v1.py")
        v1_app_path.write_text(v1_app_code)
        return v1_app_path

    def start_server(self, module_path, port, version_name):
        """Start a server process"""
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                module_path,
                "--host", "0.0.0.0",
                "--port", str(port),
                "--reload"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            self.processes.append((process, version_name, port))
            print(f"✅ {version_name} started on port {port} (PID: {process.pid})")
            
            # Monitor the process output
            def monitor_output():
                while process.poll() is None and self.running:
                    output = process.stdout.readline()
                    if output:
                        print(f"[{version_name}] {output.strip()}")
            
            monitor_thread = threading.Thread(target=monitor_output, daemon=True)
            monitor_thread.start()
            
        except Exception as e:
            print(f"❌ Failed to start {version_name}: {e}")

    def run_parallel_servers(self):
        """Run both V1.0.0 and V1.1.0 servers in parallel"""
        
        print("🚀 Starting STTM to Notebook Generator API servers...")
        print("=" * 60)
        
        # Create V1.0.0 app if it doesn't exist
        v1_app_path = self.create_v1_app()
        
        # Start V1.0.0 server
        self.start_server(
            "sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator_v1:app_v1",
            8000,
            "V1.0.0"
        )
        
        # Give V1.0.0 a moment to start
        time.sleep(2)
        
        # Start V1.1.0 server
        self.start_server(
            "sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app",
            8001,
            "V1.1.0"
        )
        
        print("=" * 60)
        print("📡 API Endpoints:")
        print(f"   V1.0.0: http://localhost:8000")
        print(f"   V1.1.0: http://localhost:8001")
        print()
        print("📋 Main Endpoints:")
        print(f"   V1.0.0: http://localhost:8000/sttm/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook")
        print(f"   V1.1.0: http://localhost:8001/sttm/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook")
        print()
        print("🏥 Health Checks:")
        print(f"   V1.0.0: http://localhost:8000/sttm/v1/health")
        print(f"   V1.1.0: http://localhost:8001/sttm/v1.1/health")
        print()
        print("📚 API Documentation:")
        print(f"   V1.0.0: http://localhost:8000/docs")
        print(f"   V1.1.0: http://localhost:8001/docs")
        print()
        print("⏹️  Press Ctrl+C to stop both servers")
        print("=" * 60)
        
        try:
            # Wait for all processes
            while self.running:
                time.sleep(1)
                # Check if any process has died
                for process, version_name, port in self.processes:
                    if process.poll() is not None:
                        print(f"⚠️  {version_name} on port {port} has stopped unexpectedly")
                        self.running = False
                        break
                        
        except KeyboardInterrupt:
            self.stop_servers()
    
    def stop_servers(self):
        """Stop all running servers"""
        print("\n🛑 Stopping servers...")
        self.running = False
        
        for process, version_name, port in self.processes:
            try:
                print(f"🛑 Stopping {version_name} on port {port}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {version_name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Force killing {version_name}...")
                process.kill()
                process.wait()
            except Exception as e:
                print(f"❌ Error stopping {version_name}: {e}")
        
        # Clean up temporary V1.0.0 file
        try:
            v1_app_path = Path("sttm_to_notebook_generator_integrated/api3_sttm_to_notebook_generator_v1.py")
            if v1_app_path.exists():
                v1_app_path.unlink()
                print("🧹 Cleaned up temporary V1.0.0 file")
        except Exception as e:
            print(f"⚠️  Could not clean up temporary file: {e}")
        
        print("✅ All servers stopped")

def main():
    """Main function to run the parallel servers"""
    runner = ParallelServerRunner()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n📡 Received signal {signum}")
        runner.stop_servers()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        runner.run_parallel_servers()
    except Exception as e:
        print(f"❌ Error running servers: {e}")
        runner.stop_servers()
        sys.exit(1)

if __name__ == "__main__":
    main() 