import logging
from pathlib import Path
import re

from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader

from notebook_generator_app.schemas.models import ServerError
from sttm_to_notebook_generator_integrated.log_handler import get_logger


BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
logger = get_logger("<API2 :: CodeGenerator>")

def sanitize_sql(sql: str) -> str:
    """This function cleans SQL code of any ``` code fences ``` and replaces {} with {{}} to prevent APIGEE Gateway Filtering"""
    sql = re.sub(r"```[a-zA-Z]*\n", "", sql)
    sql = sql.replace("```", "").strip()
    # sql = sql.replace("{", "{{").replace("}", "}}")
    return sql

def load_prompts(layer_classification: str, domain: str, product: str, txt_file: str) -> str:
    """
    This function will load system prompts for a given Layer Classification, Domain, Product, and Prompt Template.
    If None are provided, it will default to a generic-Master template for the given Layer Classification and Prompt Template.

    Args:
        layer_classification (str): 'Silver', 'Gold', or 'Silver_Dep'
        domain (str): The domain from which custom prompt templates can be created
        product (str): The products within a domain which custom prompt templates can be created
        txt_file (str): Text file name of the Prompt Template to be loaded, "system_prompt.txt", "system_prompt_validator.txt", "..."

    Returns:
        str: The prompt template based on the provided arguments
    """
    # dynamic_prompt_path = BASE_DIR / "templates" / "domain" / domain / product / txt_file
    dynamic_prompt_path = BASE_DIR / "templates" / layer_classification / domain / product / txt_file
    master_prompt_path = BASE_DIR / "templates" / layer_classification / txt_file

    if dynamic_prompt_path.exists():
        prompt_template = dynamic_prompt_path
    else:
        logger.info(f"Project-based template {dynamic_prompt_path} not found.  Falling back to generic-Master template ...")
        prompt_template = master_prompt_path

    with open(prompt_template, "r") as file:
        prompt_template = file.read()

    return prompt_template

def build_metadata_from(layer_classification: str, user_id: str, data: dict):
    """
    This function will build two metadata dictionaries used for downstream logic within this GenAI Application

    Args:
        layer_classification (str): 'Silver', 'Gold', or 'Silver_Dep'
        user_id (str): User_id to inject into rendered Notebook
        data (dict): Dictionary containing all STTM details for a given workflow

    Returns:
        dict: nb_metadata_copy - Used to inject metadata into a rendered Notebook
        dict: logic_args - Used to pass conditional arguments into downstream functions
    """
    import copy
    from datetime import datetime

    date_stamp = datetime.today().strftime("%Y-%m-%d")
    nb_metadata_copy = {}
    logic_args = {}
    for _, data_info in data.items():
        metadata = copy.deepcopy(data_info.metadata)
        target_table = metadata["target_table_name"]
        nb_metadata_copy[target_table] = metadata
        nb_metadata_copy[target_table]["user_id"] = user_id
        nb_metadata_copy["user_id"] = user_id
        nb_metadata_copy["date_stamp"] = date_stamp

        if target_table not in logic_args:
            logic_args[target_table] = {}
        if layer_classification == 'silver':
            logic_args[target_table]["source_dedupe_flag"] = nb_metadata_copy[target_table].get("source_deduplication", "N")
            logic_args[target_table]["stale_data_flag"] = nb_metadata_copy[target_table].get("stale_data_handling", "N")
        else:
            logic_args[target_table]["source_dedupe_flag"] = 'N'
            logic_args[target_table]["stale_data_flag"] = 'N'

    return nb_metadata_copy, logic_args

def render_notebook(layer_classification: str, sql_code: str, template_path: str, metadata: dict) -> str:
    """
    This function will render a Python ETL notebook from the SQL Code provided by the Model
    Args:
        layer_classification (str): 'Silver', 'Gold', or 'Silver_Dep'
        sql_code (str):
        template_path (str):
        metadata (dict):

    Returns:
        str: 
    """
    if layer_classification == 'silver':
        notebook_template = "silver_notebook_template.j2"
    elif layer_classification == 'gold':
        notebook_template = "gold_notebook_template.j2"

    sql_blocks = [
        {"comment": f"# COMMAND ----------", "query": block.strip()}
        for i, block in enumerate(sql_code.split("\n\n"))
    ]

    jinja_env = Environment(loader=FileSystemLoader(template_path))
    try:
        template = jinja_env.get_template(notebook_template)
    except Exception as e:
        logger.error(f"Error loading template: {e}")
        raise HTTPException(
            status_code=500,
            detail=ServerError(
                error_code=500,
                error_message="Template not found.  Please check template files."
            ).dict()
        )

    rendered_notebook = template.render(spark_sql_blocks=sql_blocks, metadata=metadata)
    return rendered_notebook
