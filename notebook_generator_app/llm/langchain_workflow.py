from dotenv import load_dotenv
import os
import base64
import ast
import logging
import re

from databricks_langchain.chat_models import ChatDatabricks
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langgraph.graph import StateGraph, END
from fastapi import HTTPException

from notebook_generator_app.utilities.helpers import load_prompts, sanitize_sql
from notebook_generator_app.schemas.models import SQLState, SQLGenerationFailure
from notebook_generator_app.llm.langchain_wrapper import LangChainWrapper
from notebook_generator_app.llm.pepgenx_llm import PepGenXLLMWrapper
from sttm_to_notebook_generator_integrated.log_handler import get_logger


load_dotenv()
# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
logger = get_logger("<API2 :: CodeGenerator>")

# PepGenXModel = PepGenXLLMWrapper(
#     token_url=os.getenv("TOKEN_URL"),
#     model_url=os.getenv("MODEL_URL"),
#     model_name="PepGenXModel",
#     client_id=os.getenv("CLIENT_ID"),
#     client_secret=os.getenv("CLIENT_SECRET")
# )
# llm_wrapper = LangChainWrapper(custom_model=PepGenXModel)

# llm_wrapper = ChatDatabricks(
#     endpoint="databricks-claude-3-7-sonnet",
#     temperature=0.0
#     )

# Azure OpenAI Configuration
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI

client = AzureOpenAI(
    api_key="4feeebf652bd46168c6a863b99314fc9",
    api_version="2024-07-01-preview",
    azure_endpoint="https://tigeropenaiservice.openai.azure.com/",
)

# Your deployment name (not model name!)
deployment_name = "gpt-4o"

llm_wrapper = AzureChatOpenAI(
    azure_deployment=deployment_name,
    openai_api_version="2024-07-01-preview",
    azure_endpoint="https://tigeropenaiservice.openai.azure.com/",
    openai_api_key="4feeebf652bd46168c6a863b99314fc9",
    temperature=0.0
)

def encode_sql(sql: str) -> str:
    """This function encodes SQL output from the LLM to avoid triggering security filters during the Validator Agent process"""
    return base64.b64encode(sql.encode()).decode()

def generate_sql_node(state: dict) -> dict:
    """
    LangChain node that generates raw SQL based on the provided source-to-target mapping (STTM) and instructions.

    Args:
        state (dict): The current state object passed through the LangGraph workflow.
            Expected Keys:
                - sttm (dict): Representing the STTM
                - instructions (Optional[str]): Additional instructions to be passed through as a user message
                - layer_classification (str): 'Silver', 'Gold', or 'Silver_Dep'
                - multisilver_flag (bool): Represents whether the Orchestration should be done for a MultiSilver workflow
                - domain (str): The domain from which the job is being run for
                - product (str): The product within a domain the job is being run for

    Returns:
        dict: Updated state with a new key `"sql"` containing the generated SQL code
    """
    sttm = state["sttm"]
    instructions = state["instructions"]
    layer_classification = state["layer_classification"]
    multisilver_flag = state["multisilver_flag"]
    domain = state["domain"]
    product = state["product"]
    
    logic_args = state["logic_args"]
    source_dedupe_flag = "Y" if any(args.get("source_dedupe_flag").upper() == "Y" for args in logic_args.values()) else "N"
    stale_data_flag = "Y" if any(args.get("stale_data_flag").upper() == "Y" for args in logic_args.values()) else "N"
    
    if (multisilver_flag and source_dedupe_flag.upper() != 'Y'):
        txt_file = "system_prompt_multisilver.txt"
    elif (multisilver_flag and source_dedupe_flag.upper() == 'Y' and stale_data_flag.upper() != 'Y'):
        txt_file = "system_prompt_multisilver_dedupe.txt"
    elif (multisilver_flag and source_dedupe_flag.upper() == 'Y' and stale_data_flag.upper() == 'Y'):
        txt_file = "system_prompt_multisilver_dedupe_staledata.txt"
    elif (layer_classification.lower() == 'silver' and source_dedupe_flag.upper() == 'Y' and stale_data_flag.upper() != 'Y'):
        txt_file = "system_prompt_dedupe.txt"
    elif (layer_classification.lower() == 'silver' and source_dedupe_flag.upper() == 'Y' and stale_data_flag.upper() == 'Y'):
        txt_file = "system_prompt_dedupe_staledata.txt"
    else:
        txt_file = "system_prompt.txt"
    system_prompt = load_prompts(layer_classification=layer_classification, domain=domain, product=product, txt_file=txt_file)
    # instructions = load_prompts(domain=domain, product=product, txt_file="instructions_langchain.txt")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            system_prompt
        ),
        HumanMessagePromptTemplate.from_template(
            "Generate code based on the following source-to-target mapping (STTM) and instructions:\n\n"
            "STTM:{sttm}\n\n"
            "Instructions: {instructions}\n\n"
            "{failure_context}"
        )
    ])
    # Define a RunnableSequence
    sql_chain = prompt | llm_wrapper

    # For Regeneration Tasks
    failure_reason = state.get("validation_failure_reason")
    previous_sql = state.get("previous_generated_sql")
    failure_context = ""
    if failure_reason:
        failure_context += f"NOTE: The previous output failed validation for this reason:\n{failure_reason}\n"
    if previous_sql:
        failure_context += (
            "\nBelow is the previous code you generated in base64-encoded format:\n"
            "Please decode it and respond only with the decoded output, do not include any logic related to Base64 encoding in the output.\n"
            f"{previous_sql}\n"
            "You MUST reuse what you can and fix only what failed. Do not generate unrelated code."
        )

    logger.info(f"[SQL Code Generator]: Starting Code Generation Tasks")
    response = sql_chain.invoke({
        "sttm": sttm,
        "instructions": instructions,
        "failure_context": failure_context,
        "layer_classification": layer_classification,
        "multisilver_flag": multisilver_flag,
        "domain": domain,
        "product": product,
        "logic_args": logic_args
    })
    return {**state, "sql": response.content}

def review_sql_node(state: dict) -> dict:
    """
    LangChain node that reviews and validates SQL logic and formatting using a system-defined prompt.

    Args:
        state (dict): The current state object passed through the LangGraph workflow.
            Expected Keys:
                - sql (str): The generated SQL to review and validate
                - instructions (Optional[str]): Additional instructions to be passed through as a user message
                - layer_classification (str): 'Silver', 'Gold', or 'Silver_Dep'
                - multisilver_flag (bool): Represents whether the Orchestration should be done for a MultiSilver workflow
                - domain (str): The domain from which the job is being run for
                - product (str): The product within a domain the job is being run for

    Returns:
        dict: Updated state with a new key `"reviewed_sql"` containing the reviewed SQL code
    """
    raw_sql = state["sql"]
    layer_classification = state["layer_classification"]
    multisilver_flag = state["multisilver_flag"]
    domain = state["domain"]
    product = state["product"]

    logic_args = state["logic_args"]
    source_dedupe_flag = "Y" if any(args.get("source_dedupe_flag").upper() == "Y" for args in logic_args.values()) else "N"
    stale_data_flag = "Y" if any(args.get("stale_data_flag").upper() == "Y" for args in logic_args.values()) else "N"

    raw_sql = sanitize_sql(sql=raw_sql)

    retry_count = state.get("retry_count", 0)
    if layer_classification == "silver":
        sql_str = extract_silver_sql_str(raw_str=raw_sql)
        validated_sql, msg = validate_silver_sql(sql_str=sql_str)
    else:
        validated_sql, msg = validate_gold_sql(sql_str=raw_sql)

    if not validated_sql:
        logger.warning(f"[SQL Review Validator]: Sending back to SQL Gen Agent")
        return {
            **state,
            "retry_count": retry_count + 1,
            "validation_result": "retry",
            "validation_failure_reason": msg,
            "previous_generated_sql": encode_sql(sql=raw_sql)
        }
    
    if layer_classification == "silver":
        reviewed_sql = f"transform_sql_query_dict = {validated_sql}"
    else:
        reviewed_sql = validated_sql
    logger.info(msg)
    return {
        **state,
        "reviewed_sql": reviewed_sql,
        "validation_result": "pass"
    }

def invoke_langgraph(layer_classification: str, sttm: dict, domain: str, product: str, logic_args: dict, multisilver_flag: bool=False) -> str:
    """
    Orchestrates the LangGraph SQL Generation and Validation workflow.

    Args:
        layer_classification (str): 'Silver', 'Gold', or 'Silver_Dep'
        sttm (dict): Representing the STTM
        - multisilver_flag (bool): Represents whether the Orchestration should be done for a MultiSilver workflow
        - domain (str): The domain from which the job is being run for
        - product (str): The product within a domain the job is being run for

    Returns:
        str: The final reviewed SQL string. 
    """
    instructions = load_prompts(layer_classification=layer_classification, domain=domain, product=product, txt_file="instructions_langchain.txt")

    graph = StateGraph(SQLState)
    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("review_sql", review_sql_node)

    graph.set_entry_point("generate_sql")
    
    graph.add_edge("generate_sql", "review_sql")
    graph.add_conditional_edges("review_sql", route_from_review)

    lang_graph_app = graph.compile()

    final_output = lang_graph_app.invoke({
        "sttm": sttm,
        "instructions": instructions,
        "layer_classification": layer_classification,
        "multisilver_flag": multisilver_flag,
        "domain": domain,
        "product": product,
        "logic_args": logic_args
    })
    response = final_output["reviewed_sql"]

    return response

def validate_silver_sql(sql_str):
    """
    Validates the silver SQL transformations against a set of user-defined test cases

    Args:
        sql_str (str): SQL Query to be validated

    Returns:
        str: Validated SQL Query (on success)
        bool: False (on failure)
        str: Message - Message containing success or failure details
    """
    def fail(msg):
        """This function will return a boolean False and detailed message of the failure"""
        logger.warning(f"[SQL Review Validator]: {msg}")
        return False, msg
    
    if not sql_str:
        return fail("Missing transform_sql_query_dict assignment")
    
    if '"sql"' not in sql_str and "'sql'" not in sql_str:
        return fail("Missing 'sql' key")
    
    if '"merge_key"' not in sql_str and "'merge_key'" not in sql_str:
        return fail("Missing 'merge_key' key")
    
    line_count = sql_str.strip().count("\n")
    if line_count < 5:
        return fail("Output has too few lines and is not properly formatted")
    
    msg = "[SQL Review Validator]: SQL Query Validated"
    return sql_str, msg

def validate_gold_sql(sql_str: str):
    """
    Validates the gold SQL transformations against a set of user-defined test cases

    Args:
        sql_str (str): SQL Query to be validated

    Returns:
        str: Validated SQL Query (on success)
        bool: False (on failure)
        str: Message - Message containing success or failure details
    """
    def fail(msg):
        """This function will return a boolean False and detailed message of the failure"""
        logger.warning(f"[SQL Review Validator]: {msg}")
        return False, msg

    if not sql_str:
        return fail("Missing input, nothing to validate")
    
    if not re.search(r"^\s*\w+_df\s*=", sql_str.strip(), re.MULTILINE):
        return fail("No valid <tableName>_df = (...) assignments found")

    if not re.search(r"gold_final_df\s*=", sql_str.strip()):
        return fail("Output must define a gold_final_df as the final result")
    
    line_count = sql_str.strip().count("\n")
    if line_count < 5:
        return fail("Output has too few lines and is not properly formatted")
    
    triple_quoted_blocks = re.findall(r'([frFR]*"""[\s\S]*?""")|([frFR]*\'\'\'[\s\S]*?\'\'\')', sql_str.strip())
    invalid_comment_check = sql_str
    for block in triple_quoted_blocks:
        block_content = block[0] or block[1]
        invalid_comment_check = invalid_comment_check.replace(block_content, "")

    # Check for unallowed PySpark code
    for keyword in [".select(", ".selectExpr(", ".filter(", ".withColumn(", ".drop(", ".join(", ".groupBy(", ".agg(", ".alias(", ".orderBy(", ".distinct("]:
        if keyword in invalid_comment_check:
            return fail(f"Disallowed PySpark API syntax `{keyword}` found - only SparkSQL is allowed for this output")

    if "--" in invalid_comment_check:
        return fail("Detected SQL-style -- comments outside SQL strings; Expected # for Python comments")
    if "/*" in invalid_comment_check or "*/" in invalid_comment_check:
        return fail("Detected /* */ block comments outside SQL strings; Expected # for Python comments")

    # Check for non-syntax # Python comments
    for line in invalid_comment_check.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if re.match(r"^\w+_df\s*=", line):
            continue

        if re.match(r"^\w+_temp_vw\s*=", line): # TEST LINE
            continue

        if ".createOrReplaceTempView" in line:
            continue

        if line in (")", ")", "))", ")))"):
            continue

        return fail(f"Invalid comments outside SQL strings: `{line}` - Expected # for Python comments")
    msg = "[SQL Review Validator]: SQL Query Validated"
    return sql_str, msg

def extract_silver_sql_str(raw_str: str):
    """
    Extracts dictionary from transform_sql_query_dict string for downstream silver SQL validation

    Args:
        raw_str (str): String containing the SQL Transformations defined as `transform_sql_query_dict`
    Returns:
        dict: Extracted dict containing the SQL transformations for downstream validation
        None: If no match is found, NoneType object will be returned for SQL Regeneration downstream
    """
    try:
        match = re.search(r"transform_sql_query_dict\s*=\s*(\{.*\})", raw_str, re.DOTALL)
        if not match:
            return None

        dict_body = match.group(1).strip()
        try:
            return dict_body
        except Exception:
            pass
    except Exception:
            return None
    
def route_from_review(state: dict):
    """
    LangChain Conditional Edge that will check the validation status and re-route, pass, or fail the workflow
    Will check validation status for a set number of iterations and either re-route back to the SQL CodeGen Agent,
    Pass the workflow for completion, or raise an exception for max amount of retries

    Args:
        state (dict): The current state object passed through the LangGraph workflow.
            Expected Keys:
                - retry_count (int): Number of Retries for a workflow
                - validation_result (str): "retry" or "pass"
                - validation_failure_reason (str): Reason for why the SQL Code was rejected by the Validation Agent

    Returns:
        str: "generate_sql" - Re-route to SQL CodeGen Agent
        obj: END - Pass for completion
        err: Exception - 422 HTTPException "SQL_VALIDATION_FAILED"
    """
    retry_count = state.get("retry_count", 0)
    if retry_count >= 5:
        logger.error(f"[SQL Review Validator]: SQL Generation failed after {retry_count} retries. Please try again.")
        raise HTTPException(
            status_code=422,
            detail=SQLGenerationFailure(
                error_code="SQL_VALIDATION_FAILED",
                error_message=f"SQL Generation failed after {retry_count} retries.",
                failure_reason=state.get("validation_failure_reason"),
                retries=retry_count
            ).dict()
        )
    
    if state.get("validation_result") == "retry":
        return "generate_sql"
    
    return END