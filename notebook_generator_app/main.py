import json
import os
import io
import re

from dotenv import load_dotenv
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException

from notebook_generator_app.utilities.helpers import render_notebook, build_metadata_from
from notebook_generator_app.llm.langchain_workflow import invoke_langgraph
from sttm_to_notebook_generator_integrated.read_env_var import *
from notebook_generator_app.schemas.models import (
    PromptRequestModel,
    PromptResponseModel,
    ServerError,
    ValidationError,
    HTTPValidationError
)
from sttm_to_notebook_generator_integrated.log_handler import get_logger


# load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
logger = get_logger("<API2 :: CodeGenerator>")

appName = os.environ.get('rootContext')
# appName = "silver-codegen-genai"
# Initialize FastAPI app
app2 = APIRouter()

# title="Silver Code Generator",
#     description="PepGenX (OpenAI) API Wrapper",
#     version="1.0"


@app2.post(f"/{appName}/api/v1/edf/genai/codegenservices/generate-notebook",
    summary="Generate ETL Notebook using MultiAgent through OpenAI",
    response_model=PromptResponseModel,
    response_description="The path to the generated ETL Notebook from OpenAI",
    responses={
        400: {"model": ValidationError, "description": "Bad Request - Invalid input"},
        422: {"model": HTTPValidationError, "description": "Validation Error - Schema mismatch"},
        500: {"model": ServerError, "description": "Internal Server Error"}
    }
)
async def generate_response(request: PromptRequestModel):
    logger.info("Generate Notebook API Initialized")
    meta = request.notebook_metadata_json
    data = request.content

    user_id = meta.user_id
    layer_classification = meta.table_load_type.lower()
    domain = meta.domain.lower()
    product = meta.product.lower()

    target_table_count = len(data)
    if target_table_count == 1:
        multisilver_flag = False
    elif target_table_count > 1:
        multisilver_flag = True
    else:
        raise HTTPException(
            status_code=422,
            detail=ValidationError(
                type="missing",
                loc=["body", "data"],
                msg="STTM Data can not be empty.  Please check STTM files."
            ).dict()
        )
    
    nb_metadata_copy, logic_args = build_metadata_from(
        layer_classification=layer_classification,
        user_id=user_id,
        data=data
    )
 
    result = invoke_langgraph(
        layer_classification=layer_classification,
        sttm=data,
        domain=domain,
        product=product,
        logic_args=logic_args,
        multisilver_flag=multisilver_flag
    )

    template_path =  BASE_DIR / "templates" / layer_classification
    notebook_str = render_notebook(
        layer_classification=layer_classification,
        sql_code=result,
        template_path=template_path,
        metadata=nb_metadata_copy
    )
    logger.info("Notebook generated successfully")
    return PromptResponseModel(
        success=True,
        message="Notebook generated successfully.",
        notebook_id="TODO",
        notebook_name="generated_notebook.py",
        data=notebook_str
    )

# app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# Run the application
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)