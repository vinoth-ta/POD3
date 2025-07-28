from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from typing import List
import json
from .read_env_var import *

async def get_client_ip(request: Request):
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # The first IP in the list is the real client IP
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        # Fallback to direct client IP
        ip = request.client.host
    # print(ip)
    return ip

# Import the APIRouters from your two API files
from .api1_json_converter import app1 as json_converter_router
from notebook_generator_app.main import app2 as notebook_generator_router
from notebook_generator_app.schemas.models import PromptRequestModel, PromptResponseModel, MetaInfo # Import necessary models from api2
from .log_handler import get_logger
logger = get_logger("<API3 :: Encapsulator>")

# Initialize the main FastAPI application
app = FastAPI(
    title="Combined API for STTM to Notebook Generation",
    description="Orchestrates the conversion of STTM Excel to JSON and then generates an ETL notebook.",
    version="1.0.0"
)

# Include the routers from your individual API files
# This makes their endpoints available under the main FastAPI application
app.include_router(json_converter_router)
app.include_router(notebook_generator_router)
appName = os.environ.get('rootContext')

# Define a new endpoint in the main app that orchestrates the flow
@app.post(f"/{appName}/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook",
          summary="Full Process: Convert STTM to JSON and Generate Silver Notebook",
          response_model=PromptResponseModel,
          response_description="The path to the generated ETL Notebook and status.",
          responses={
              400: {"description": "Bad Request - Invalid input"},
              422: {"description": "Validation Error - Schema mismatch"},
              500: {"description": "Internal Server Error"}
          })
async def full_process_generate_notebook(
    request: Request,
    sttm_metadata_json: str = Form(..., description="JSON string of a list of dictionaries containing STTM metadata."),
    sttm_files: List[UploadFile] = File(..., description="List of STTM Excel files to be processed."),
    notebook_metadata_json: str = Form(..., description="JSON string containing metadata for the notebook generation (user_id, table_load_type, domain, product, notebook_name).")
):
    """
    This endpoint orchestrates the entire process:
    1. Calls the `build-json-mapping-from-excel-no-baseline` endpoint (from `api1_json_converter`).
    2. Takes the output of the first step and formats it as input for the `generate-silver-notebook` endpoint (from `api2_notebook_generator(app/main)`).
    3. Calls the `generate-silver-notebook` endpoint.
    4. Returns the final response from the notebook generation step.
    """
    client_ip =await get_client_ip(request)
    logger.info(f"Request received from IP: {client_ip}")
    try:
        # Step 1: Call the logic of api1_json_converter
        # We need to directly call the async function from api1_json_converter.py
        # and pass the arguments it expects.
        # We import the `orchestrate_json_sttm` function directly.
        from .api1_json_converter import orchestrate_json_sttm as process_sttm_to_json

        # Await the execution of the first API's logic
        json_conversion_output =await process_sttm_to_json(
            sttm_metadata_json=sttm_metadata_json,
            sttm_files=sttm_files,
            notebook_metadata_json=notebook_metadata_json # Pass this through, as api1 now modifies it
        )
        #print(type(json_conversion_output))
        logger.debug(json_conversion_output)
        #print(json_conversion_output.keys())
        
        # Step 2: Prepare the output of api1 as input for api2
        # json_conversion_output is already structured as required by PromptRequestModel
        # after api1's modification to notebook_metadata_json
        
        # Ensure notebook_metadata_json from the first step is properly typed
        # It's already a dictionary in json_conversion_output, but Pydantic expects MetaInfo model
        # Re-parse it to ensure it matches the Pydantic model's strict typing if needed
        # Or, ideally, api1's `notebook_metadata_json` should directly return the MetaInfo model
        # For simplicity, we'll assume it's directly compatible or cast it.
        
        # Since `json_conversion_output` contains `notebook_metadata_json` as a dict
        # and `content` as a dict of DataInfo, we can directly construct PromptRequestModel
        
        # Parse the notebook_metadata_json from the first step's output to MetaInfo
        # This handles the unique_ID added by the first API
        processed_notebook_meta = json_conversion_output["notebook_metadata_json"]
        
        # Instantiate the PromptRequestModel using the processed data
        # Note: The `content` from `json_conversion_output` is a dict of `DataInfo`
        # and `notebook_metadata_json` is a dict that needs to be converted to `MetaInfo`.
        
        # Correctly instantiate MetaInfo from the dictionary
        # Directly instantiate MetaInfo using the dictionary from the first API's output
        meta_info_instance = MetaInfo(**processed_notebook_meta)
        #
        #
        ## Create the PromptRequestModel instance
        prompt_request = PromptRequestModel(
            status_code=json_conversion_output["status_code"],
            notebook_metadata_json=meta_info_instance, # Use the parsed MetaInfo
            content=json_conversion_output["content"]
        )

        # Step 3: Call the logic of api2_notebook_generator
        # We need to directly call the async function from api2_notebook_generator.py
        # and pass the arguments it expects.
        # We import the `generate_response` function directly.
        
        from notebook_generator_app.main import generate_response as generate_notebook

        final_response =await generate_notebook(request=prompt_request)
        
        logger.info("Notebook generation completed successfully!")
        return final_response

    except HTTPException as e:
        message = str(e)
        logger.error(message)
        # Re-raise HTTPExceptions as they are already formatted for FastAPI
        raise e
    except Exception as e:
        message = f"An internal server error occurred: {str(e)}"
        logger.error(message)
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=message)

# Optional: Add a root endpoint for basic health check
@app.get(f"/{appName}")
async def read_root():
    return {"message": f"Welcome to the Combined STTM to Notebook Generation API!\nPlease use the path: /{appName}/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook"}