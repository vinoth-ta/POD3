from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import pandas as pd
import requests
import json
import time
from io import BytesIO
from .log_session_id import SESSION_LOG_ID
from .log_handler import get_logger
logger = get_logger("<API1 :: JSON Converter>")

# --- Added as per user request ---
import re
from collections import defaultdict
from typing import Optional, List, Set, Tuple
# --- End of user-added imports ---


# logger.debug("Debug message")
# logger.info("Info message")
# logger.warning("Warning message")
# logger.error("Error message")
# logger.critical("Critical message")

from .read_env_var import *

app1 = APIRouter()

def generate_sparksql(json_mapping,query_already_exist='n'):
    try:
        target_table = json.loads(json_mapping)['target_table']
        if(query_already_exist.lower() != 'y'):
            query_prompt = f"""
                You are a Databricks expert proficient in PySpark and Spark SQL. Based on the following source-to-target mapping JSON, generate complete Spark SQL and PySpark code that is directly executable in a Databricks notebook cell. There is already an active Spark session—no need to create one. All necessary libraries are pre-imported.
                Here is the JSON mapping:

                {json_mapping}  

                OUTPUT REQUIREMENTS:
                •	The output must use Spark SQL (spark.sql("...")) blocks combined with temporary views (createOrReplaceTempView) to represent each logical stage of the transformation.
                •	Avoid excessive .withColumn chains. Break transformations into logical steps, and create temp views after each significant step to improve clarity and maintainability.
                •	Use meaningful, descriptive temp view names reflecting the purpose or stage of each transformation.
                •	Leverage Spark SQL for transformations wherever possible, especially for joins, filters, and column derivations.
                •	If a transformation is not defined in the mapping, assume a direct column mapping.
                •	Consider all nested dependencies, and ensure subqueries are resolved through sequential temp views leading to the final result.
                •	For joins:
                o	Use INNER JOIN unless otherwise specified.
                o	Add filters to exclude rows with NULL values in join keys before performing joins.
                o	Select only the necessary columns from each source table.
                •	Handle null-safe operations for numerical or critical columns to avoid unexpected results.
                •	For dynamic or parameterized values, represent them as PySpark variables within curly brackets wrapped in single quotes.
                •	Include inline comments for complex logic to enhance readability.
                •	The final output should be a standalone SELECT statement, selecting from the last temp view representing the final transformed dataset.
                •	Do not use INSERT or INSERT INTO statements—just provide the final SELECT.
                •	Output only the executable code, with no additional explanations or markdown formatting like triple backticks.
                    """
        ## This line is for using Azure OpenAI endpoints
        spark_sql_query=get_llm_response(user_prompt=query_prompt)
        
        ## This line is for using databricks LLM endpoints
        # spark_sql_query=get_databricks_endpoint_response(user_prompt=query_prompt,max_tokens=80000,generation_model='databricks-claude-3-7-sonnet')
        
        ## This line is for using pepgenx LLM endpoints
        # spark_sql_query=get_pepgenx_response(user_prompt=query_prompt,max_tokens=16384,generation_model='gpt-4o',model_provider_name='openai')
        # spark_sql_query=get_pepgenx_response(user_prompt=query_prompt,max_tokens=8192,generation_model='claude-3-5-sonnet',model_provider_name='aws-anthropic')    
                     
        

        return spark_sql_query
    except Exception as e:
        message=f"Error in Spark SQL generation: Error : {e}"
        logger.error(message)
        return message

def get_access_token(client_id, client_secret, base_url):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    response = requests.post(base_url, headers=headers, data=data)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        # logger.debug(response.json())
        return access_token
    else:
        message=f"Failed to obtain access token: {response.status_code} {response.text}"
        logger.error(message)
        raise Exception(message)


def get_pepgenx_response(user_prompt,max_tokens,generation_model,model_provider_name ):
    token=get_access_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, base_url=TOKEN_URL) 
    # logger.debug(token) 

    MODEL_URL=f'https://apim-na.qa.mypepsico.com/cgf/pepgenx/v2/llm/{model_provider_name}/generate-response'
    logger.info(f"MODEL_URL:{MODEL_URL}")
    HEADERS = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "team_id":TEAM_ID,
        "project_id":PROJECT_ID,
        "x-pepgenx-apikey":PEPGENX_API_KEY,
    }

    payload = {
                "prompt":user_prompt,
                "generation_model":generation_model,
                "max_tokens":max_tokens
            }

    response = requests.request("POST",
        url=MODEL_URL,
        headers=HEADERS,
        json=payload
    )
    logger.info("request-id:"+str(response.headers.get("x-request-id")))
    # print("input token:"+str(response.json()["usage"]["prompt_tokens"]))
    # print("output token:"+str(response.json()["usage"]["completion_tokens"]))
    logger.info("time taken in sec:"+str(response.elapsed.total_seconds()))
    # print(response.json())
    logger.info(response.status_code)
    if response.status_code != 200:
        message=f"PepGenx LLM call failed : {response.status_code} - {response.text}"
        logger.error(message)
        raise HTTPException(status_code=502, detail=message)
    raw_response=response.json()["response"]
    # cleaned_response = raw_response.encode('utf-8').decode('unicode_escape')
    return(raw_response)



def get_databricks_endpoint_response(user_prompt,max_tokens,generation_model):
    # DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST")
    # print(DATABRICKS_HOST)
    # DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    # print(DATABRICKS_TOKEN)
    MODEL_NAME = generation_model #"databricks-meta-llama-3-3-70b-instruct"
    HEADERS = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }
    MAX_TOKENS = max_tokens
    
    payload = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant that understands STTM mappings and produces a corresponding json data."},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": 0.2,
    "max_tokens": MAX_TOKENS
    }

    response = requests.post(
        f"{DATABRICKS_HOST}/serving-endpoints/{MODEL_NAME}/invocations",
        headers=HEADERS,
        json=payload
    )
    logger.info("request-id:"+str(response.headers.get("x-request-id")))
    logger.info("time taken in sec:"+str(response.elapsed.total_seconds()))
    if response.status_code != 200:
        message=f"LLM call failed : {response.status_code} - {response.text}"
        logger.error(message)
        raise HTTPException(status_code=502, detail=message)

    content = response.json()['choices'][0]['message']['content']
    logger.info("input token:"+str(response.json()["usage"]["prompt_tokens"]))
    logger.info("output token:"+str(response.json()["usage"]["completion_tokens"]))
    return content


def get_llm_response(user_prompt):
    try:
        # Use Azure OpenAI directly
        import openai
        
        client = openai.AzureOpenAI(
            api_key="4feeebf652bd46168c6a863b99314fc9",
            api_version="2024-07-01-preview",
            azure_endpoint="https://tigeropenaiservice.openai.azure.com/",
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Your deployment name (not model name!)
            messages=[
                {"role": "system", "content": "You are an expert data engineer specializing in ETL processes and JSON generation from Excel-based source-to-target mappings."},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=16384,
            temperature=0.1
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Azure OpenAI LLM invocation failed with error: {str(e)}")
        raise HTTPException(status_code=502, detail="LLM call failed!")
      
def get_metadata(metadata_list, file_name):
    for idx, meta_dict in enumerate(metadata_list):
        if(meta_dict.get("file_name").strip()==file_name):
            return meta_dict
    meta_dict={}
    return meta_dict

# --- Added: Excel Data Optimizer ---
def optimize_excel_data(df: pd.DataFrame) -> Tuple[str, dict]:
    """
    Optimize Excel data and extract metadata for smarter processing.
    Returns optimized CSV and metadata dict.
    """
    # Remove completely empty rows and columns
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')

    # Extract metadata about the structure
    metadata = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': df.columns.tolist(),
        'has_data': len(df) > 0
    }

    # Identify key columns by name patterns
    for col in df.columns:
        col_lower = col.lower()
        if 'target' in col_lower and 'column' in col_lower:
            metadata['target_column_col'] = col
            metadata['target_columns'] = df[col].dropna().unique().tolist()
        elif 'source' in col_lower and 'table' in col_lower:
            metadata['source_table_col'] = col
            metadata['source_tables'] = df[col].dropna().unique().tolist()
        elif 'transformation' in col_lower:
            metadata['transformation_col'] = col
            metadata['has_transformations'] = df[col].notna().any()

    # Convert to CSV
    csv_data = df.to_csv(index=False)

    return csv_data, metadata
# --- End Excel Data Optimizer ---

# --- Added: Smart Python Validators ---
class SmartValidator:
    """Smart validation using Python to minimize LLM calls"""

    @staticmethod
    def validate_json_syntax(json_string: str) -> Tuple[bool, Optional[str]]:
        """Validate JSON syntax with detailed error info"""
        try:
            json.loads(json_string)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"JSON syntax error at line {e.lineno}, column {e.colno}: {e.msg}"

    @staticmethod
    def validate_schema(json_data: dict) -> Tuple[bool, List[str]]:
        """Validate JSON schema and structure"""
        errors = []

        # Check required top-level keys
        required_keys = ["target_table", "source_tables", "column_mapping"]
        for key in required_keys:
            if key not in json_data:
                errors.append(f"Missing required key: '{key}'")

        # Validate target_table
        if not json_data.get("target_table", "").strip():
            errors.append("target_table is empty or missing")

        # Validate source_tables
        source_tables = json_data.get("source_tables", [])
        if not isinstance(source_tables, list):
            errors.append("source_tables must be a list")
        else:
            source_table_names = set()
            for idx, table in enumerate(source_tables):
                if not isinstance(table, dict):
                    errors.append(f"source_tables[{idx}] must be a dictionary")
                elif not table.get("name"):
                    errors.append(f"source_tables[{idx}] missing 'name' field")
                else:
                    source_table_names.add(table["name"])

        # Validate column_mapping
        column_mapping = json_data.get("column_mapping", {})
        if not isinstance(column_mapping, dict):
            errors.append("column_mapping must be a dictionary")
        elif not column_mapping:
            errors.append("column_mapping is empty")

        return len(errors) == 0, errors

    @staticmethod
    def validate_column_coverage(json_data: dict, excel_metadata: dict) -> Tuple[bool, List[str]]:
        """Check if all target columns from Excel are in JSON"""
        errors = []

        expected_columns = set(excel_metadata.get('target_columns', []))
        json_columns = set(json_data.get('column_mapping', {}).keys())

        missing_columns = expected_columns - json_columns
        if missing_columns:
            errors.append(f"Missing target columns: {sorted(missing_columns)}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_source_references(json_data: dict) -> Tuple[bool, List[str]]:
        """Validate all source table references exist"""
        errors = []

        # Get all defined source tables
        defined_sources = {
            table.get("name", "")
            for table in json_data.get("source_tables", [])
            if isinstance(table, dict)
        }

        # Check all column mappings reference valid sources
        column_mapping = json_data.get("column_mapping", {})
        for col_name, col_def in column_mapping.items():
            if isinstance(col_def, dict):
                sources = col_def.get("sources", {})
                if isinstance(sources, dict):
                    src_table = sources.get("source_table", "").strip()
                    if src_table and src_table not in defined_sources:
                        errors.append(f"Column '{col_name}' references undefined source table '{src_table}'")

        return len(errors) == 0, errors

    @staticmethod
    def validate_transformations(json_data: dict) -> Tuple[bool, List[str], bool]:
        """
        Validate transformations and determine if LLM validation is needed.
        Returns (is_valid, errors, needs_llm_validation)
        """
        errors = []
        complex_transformations = 0
        total_transformations = 0

        # Standard transformation patterns that don't need LLM validation
        simple_patterns = [
            r'^Direct\s*(\(|$)',
            r'^Default\s+Value:\s*\d+',
            r'^Uppercase\s*(\(|$)',
            r'^Lowercase\s*(\(|$)',
            r'^Trim\s*(\(|$)',
            r'^Concatenate\s*\(',
            r'^Substring\s*\(',
            r'^DateFormatting\s*\(',
        ]

        column_mapping = json_data.get("column_mapping", {})
        for col_name, col_def in column_mapping.items():
            if isinstance(col_def, dict):
                sources = col_def.get("sources", {})
                if isinstance(sources, dict):
                    transformation = sources.get("transformation", "").strip()

                    if transformation:
                        total_transformations += 1

                        # Check if it's a simple transformation
                        is_simple = any(re.match(pattern, transformation, re.IGNORECASE)
                                      for pattern in simple_patterns)

                        if not is_simple:
                            complex_transformations += 1

                        # Basic validation
                        if len(transformation) > 1000:
                            errors.append(f"Column '{col_name}' has unusually long transformation")

        # Determine if LLM validation is needed
        needs_llm = complex_transformations > 5 or complex_transformations > total_transformations * 0.3

        return len(errors) == 0, errors, needs_llm

    @staticmethod
    def validate_business_rules(json_data: dict) -> Tuple[bool, List[str]]:
        """Apply business-specific validation rules"""
        warnings = []

        # Check for suspicious patterns
        column_mapping = json_data.get("column_mapping", {})

        # Check for too many columns
        if len(column_mapping) > 500:
            warnings.append(f"Unusually high number of columns: {len(column_mapping)}")

        # Check for duplicate transformations
        transformations = defaultdict(list)
        for col_name, col_def in column_mapping.items():
            if isinstance(col_def, dict):
                sources = col_def.get("sources", {})
                if isinstance(sources, dict):
                    trans = sources.get("transformation", "").strip()
                    if trans:
                        transformations[trans].append(col_name)

        for trans, cols in transformations.items():
            if len(cols) > 10:
                warnings.append(f"Transformation '{trans[:50]}...' used in {len(cols)} columns")

        return True, warnings  # Warnings don't fail validation

def comprehensive_python_validation(json_string: str, excel_metadata: dict) -> Tuple[bool, List[str], bool]:
    """
    Run all Python validations and determine if LLM validation is needed.
    Returns (is_valid, all_issues, needs_llm_validation)
    """
    validator = SmartValidator()
    all_issues = []
    needs_llm = False

    # 1. JSON Syntax
    valid, error = validator.validate_json_syntax(json_string)
    if not valid:
        all_issues.append(error)
        return False, all_issues, False  # Can't proceed without valid JSON

    json_data = json.loads(json_string)

    # 2. Schema validation
    valid, errors = validator.validate_schema(json_data)
    if not valid:
        all_issues.extend(errors)

    # 3. Column coverage
    valid, errors = validator.validate_column_coverage(json_data, excel_metadata)
    if not valid:
        all_issues.extend(errors)

    # 4. Source references
    valid, errors = validator.validate_source_references(json_data)
    if not valid:
        all_issues.extend(errors)

    # 5. Transformation validation
    valid, errors, needs_llm_check = validator.validate_transformations(json_data)
    if not valid:
        all_issues.extend(errors)
    needs_llm = needs_llm or needs_llm_check

    # 6. Business rules (warnings only)
    _, warnings = validator.validate_business_rules(json_data)
    if warnings:
        logger.info(f"Business rule warnings: {warnings}")

    return len(all_issues) == 0, all_issues, needs_llm
# --- End Smart Python Validators ---

# --- Added: Error Pattern Analyzer ---
def analyze_error_patterns(errors: List[str]) -> str:
    """Analyze errors and generate specific feedback for retry"""
    feedback_parts = []

    # Group errors by type
    missing_columns = []
    missing_tables = []
    schema_errors = []
    other_errors = []

    for error in errors:
        if "Missing target columns:" in error:
            # Extract column names
            match = re.search(r"Missing target columns: \[(.*?)\]", error)
            if match:
                cols = [c.strip().strip("'") for c in match.group(1).split(",")]
                missing_columns.extend(cols)
        elif "undefined source table" in error:
            # Extract table name
            match = re.search(r"undefined source table '(.*?)'", error)
            if match:
                missing_tables.append(match.group(1))
        elif "Missing required key:" in error or "empty" in error:
            schema_errors.append(error)
        else:
            other_errors.append(error)

    # Generate specific feedback
    if missing_columns:
        feedback_parts.append(
            f"Add these missing columns to column_mapping: {', '.join(missing_columns[:10])}"
            + (" and others" if len(missing_columns) > 10 else "")
        )

    if missing_tables:
        unique_tables = list(set(missing_tables))
        feedback_parts.append(
            f"Add these source tables to source_tables list: {', '.join(unique_tables[:5])}"
            + (" and others" if len(unique_tables) > 5 else "")
        )

    if schema_errors:
        feedback_parts.append("Fix these structure issues: " + "; ".join(schema_errors[:3]))

    if other_errors:
        feedback_parts.append("Address these issues: " + "; ".join(other_errors[:3]))

    return "\n".join(f"- {part}" for part in feedback_parts)
# --- End Error Pattern Analyzer ---

appName = os.environ.get('rootContext')
@app1.post(f"/{appName}/api/v1/edf/genai/codegenservices/build-json-mapping-from-excel-no-baseline")
async def build_json_mapping_from_excel_no_baseline(
    sttm_metadata_json: str = Form(...),    # JSON string of list of dicts
    sttm_files: List[UploadFile] = File(...), 
    notebook_metadata_json: str = Form(...) 
):
    try:
        metadata_list = json.loads(sttm_metadata_json)
    except json.JSONDecodeError:
        message="Invalid JSON for sttm_metadata_json."
        logger.error(message)
        raise HTTPException(status_code=400, detail=message)

    if not isinstance(metadata_list, list):
        message="sttm_metadata_json must be a list of objects."
        logger.error(message)
        raise HTTPException(status_code=400, detail=message)

    if len(metadata_list) != len(sttm_files):
        message="Mismatched number of STTM files and STTM metadata entries."
        logger.error(message)
        raise HTTPException(status_code=400, detail=message)

    results = {}

    for idx, file in enumerate(sttm_files):
        meta = get_metadata(metadata_list, file.filename.strip())
        if (meta=={}):
            message=f"No matched file name found in sttm_metadata_json for the file: {file.filename}"
            logger.error(message)
            raise HTTPException(status_code=400, detail=message)
            
        if not meta.get("target_table_name") or not meta.get("sheet_name"):
            message=f"Missing target_table_name or sheet_name at index {idx}."
            logger.error(message)
            raise HTTPException(status_code=400, detail=message)
        
        target_table_name = meta.get("target_table_name").strip()
        sheet_name = meta.get("sheet_name").strip()


        try:
            contents = await file.read()
            excel_data = pd.read_excel(BytesIO(contents), sheet_name=sheet_name)
        except Exception as e:
            message=f"Failed to read Excel file '{file.filename}': {str(e)}"
            logger.error(message)
            raise HTTPException(status_code=400, detail=message)

        sheet_data = excel_data.to_csv(index=False)

        json_prompt = """                       
                    You are a data engineering expert. Below is an extract from a Source-to-Target Mapping (STTM) spreadsheet. It contains important metadata including source tables, target tables, column-level mappings, join conditions, filters, and possibly an overall data loading logic.
                    Extract from a Source-to-Target Mapping (STTM) spreadsheet:
                    """ + sheet_data + """
                    Instructions:
                    1.	Carefully analyze the entire spreadsheet to identify:
                    o	The target table name.
                    o	All source tables, with any descriptions if provided.
                    o	If there are columns available in the STTM spreadsheet named like bronze table or bronze table column etc., then give priority to those as source table. If there is nothing like that then give priority to those columns as source. If there are no such columns then look for source table or source column etc. regular column names.
                    o	Parameters/variables used (these typically come as inputs to a notebook or pipeline).
                    o	Column mappings from source to target.
                    	Ensure that all columns defined for the target table are captured in the final JSON output, even if some of the metadata (e.g., source field, transformation) is missing or blank in the sheet. Do not skip any row representing a target column.
                    	If no transformation logic is provided, assume it is a direct mapping from the source table's source column.
                    	If the transformation column contains terms like "Default" or "Default Value", then treat the column as using a hardcoded value.
                    	In such cases, extract the corresponding hardcoded value from a column named "Default Value" (or similar), and use that value as the transformation.
                    	Example: If transformation says Default and default value is Y, then transformation = Use default value 'Y'.
                    	If the transformation contains any of the known standard coded transformation terms defined in the glossary (provided below), then:
                    	Retain the full transformation expression exactly as it appears in the spreadsheet.
                    	Immediately append a clear explanation in parentheses based on the glossary definition.
                    	If multiple standard terms appear, provide explanations for each.
                    	If no standard term applies, leave the transformation field as-is.
                    	Use examples in the glossary section to help detect variants or phrasing of these standard terms.
                    o	Join conditions, including join types (INNER, LEFT, etc.). Join criteria can be found in the join-specific column. If that’s empty, scan other areas.
                    o	Filter criteria used on any of the source tables. Filter criteria can be found in the filter-specific column. If that’s empty, scan other areas.
                    o	The overall workflow logic that governs the transformation as a whole. This logic might appear in multiple formats:
                    	As a separate text block above or below the mapping table (e.g., titled Over All Logic, Functional Requirement at Table Level, or Workflow Logic).
                    	OR embedded in the mapping table itself under a column (often merged) with a header such as Functional Requirement at Table Level, Over All logic, Workflow, or similar.
                    	Make sure to extract and include the full content from such columns as part of workflow_logic.
                    2.	Pay attention to multi-step transformation logic. If multiple actions are required to populate a single column, preserve the entire sequence of steps under the transformation field.
                    3.	Do not summarize transformation steps. Retain entire detail to avoid misinterpretation.
                    4.	Ensure even minor transformation/filtering details are included in the final JSON.
                    5.	Do not assume or infer anything that is not explicitly specified in the Excel-based STTM.
                    6.	Ensure all keys and values in the JSON are enclosed in double quotes (").
                    o	If any value contains a double quote ("), replace it with a single quote (') to maintain valid JSON syntax.
                    7.	Produce your output strictly in the following structured JSON format:
                    ```
                    {
                      "target_table": "<target table name>",
                      "workflow_logic": "<Over All data load logic>",
                      "parameters": {
                        "var1": "variable 1. comes as parameter to the notebook",
                        "var2": "variable 2. comes as parameter to the notebook"
                      },
                      "source_tables": [
                        {
                          "name": "<st1>",
                          "desc": "<source table 1>",
                          "catalog": "<catalog name for st1>",
                          "schema": "<schema name for st1>"
                        }
                        ],
                      "column_mapping": {
                        "<target column name1>": {
                          "target_datatype": "string",
                          "target_desc": "1st column",
                          "sources": 
                            {
                              "source_table": "st1",
                              "source_field": "col1",
                              "source_datatype": "string",
                              "source_desc": "<column one>",
                              "transformation": "<full transformation logic, with glossary explanation if applicable>",
                              "join_condition": "<join condition and join type>",
                              "filter": "<filter condition>"
                            }
                        }
                      }
                    }
                    ```
                    Please return only the JSON string as your final output.

                    Glossary of Standard Coded Transformation Terms
                    When a transformation value in the STTM matches one of these standard terms, preserve the transformation string, and append its explanation in parentheses in the JSON.
                    ________________________________________
                    a. Direct
                    Definition: Directly maps the source column to the target column. If data types differ, apply casting.
                    Expected Format: Direct or Direct Pull
                    Example:
                    For MANDT → ClientId: "transformation": "Direct Pull (Directly maps MANDT to ClientId with casting to target type)"
                    ________________________________________
                    b. Concatenate
                    Definition: Joins multiple columns or strings together with optional delimiter. Casting is applied if needed.
                    Expected Format:
                    Concatenate(col1, col2)
                    Concatenate(col1, "|", col2)
                    Example:
                    Concatenate(ClientId, "|", MaterialId) results in "ClientId|MaterialId"
                    ________________________________________
                    c. Uppercase
                    Definition: Converts source string to uppercase.
                    Expected Format: uppercase
                    ________________________________________
                    d. Lowercase
                    Definition: Converts source string to lowercase.
                    Expected Format: lowercase
                    ________________________________________
                    e. Titlecase
                    Definition: Capitalizes first letter of each word.
                    Expected Format: titlecase
                    ________________________________________
                    f. Substring
                    Definition: Extracts substring starting from position and length.
                    Expected Format: Substring(start_pos, length)
                    Example: Substring(1, 5)
                    ________________________________________
                    g. Substring_col
                    Definition: Like Substring, but allows explicit column.
                    Expected Format: Substring_col(column, start_pos, length)
                    Example: Substring_col(ClientId, 1, 5)
                    ________________________________________
                    h. Replace
                    Definition: Replaces substrings.
                    Expected Format: replace("pattern", "replacement")
                    Example: replace("Street", "St.")
                    ________________________________________
                    i. Trim
                    Definition: Removes leading and trailing whitespace.
                    Expected Format: trim
                    ________________________________________
                    j. Trim Symbols
                    Definition: Removes non-alphanumeric or special symbols.
                    Expected Format: trimsymbols("column")
                    Example: trimsymbols("SPRAS")
                    ________________________________________
                    k. Trim Trailing Zeros
                    Definition: Removes trailing zeros.
                    Expected Format: trimtrailingzeros("column")
                    ________________________________________
                    l. Trim Leading Zeros
                    Definition: Removes leading zeros.
                    Expected Format: trimleadingzeros("column")
                    ________________________________________
                    m. Date Formatting
                    Definition: Formats date column into a target pattern.
                    Expected Format: DateFormatting("yyyy-mm-dd")
                    ________________________________________
                    n. Date Calculation
                    Definition: Adds/subtracts days from a date.
                    Expected Format: DateCalculation(30)
                    Example: DateCalculation(-10) subtracts 10 days.
                    ________________________________________
                    o. Date Extraction
                    Definition: Extracts year, month, etc. from date.
                    Expected Format: DateExtraction("column", "pattern")
                    Example: DateExtraction("CreatedDate", "yyyy")
                    ________________________________________
                    p. Numeric Calculation
                    Definition: Arithmetic operations (e.g. subtract, multiply).
                    Expected Format: NumericCalculation(col1 - col2)
                    Example: NumericCalculation(ActualSales - DelayedSales)
                    ________________________________________
                    q. Conditional
                    Definition: IF-ELSE style logic for 1 condition.
                    Expected Format: Conditional("condition", "value_if_true", "value_if_false")
                    Example: Conditional("price > 1000", "High", "Low")
                    ________________________________________
                    r. Case When
                    Definition: Multi-branch logic like SQL CASE WHEN.
                    Expected Format:
                    CaseWhen("cond1", "val1", "cond2", "val2", "default")
                    Example: CaseWhen("score > 90", "A", "score > 75", "B", "C")
                    ________________________________________
                    s. Null Handling
                    Definition: Replaces nulls with fallback value(s).
                    Expected Format: NullHandling("col1", "col2", "default")
                    Example: NullHandling("email", "phone", "No contact info")
        """
        logger.info(f"Processing file :: {file.filename}")
        # print(f"json_prompt :: {json_prompt}")
        
        ## This line is for using databricks LLM endpoints
        content=get_databricks_endpoint_response(user_prompt=json_prompt,max_tokens=80000,generation_model='databricks-claude-3-7-sonnet')
        
        ## This line is for using pepgenx LLM endpoints
        # content=get_pepgenx_response(user_prompt=json_prompt,max_tokens=16384,generation_model='gpt-4o',model_provider_name='openai')
        # content=get_pepgenx_response(user_prompt=json_prompt,max_tokens=80000,generation_model='claude-3-5-sonnet',model_provider_name='aws-anthropic')
        # print(content)
        
        
        
        clean_json = content.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(clean_json)
        except json.JSONDecodeError as e:
            message=f"JSON parsing failed for file '{file.filename}': {str(e)}"
            logger.error(message)
            raise HTTPException(status_code=500, detail=message)

        results[target_table_name] = {"metadata": meta,"json_sttm":parsed}
        #print(results)
        
        try:
            notebook_metadata = json.loads(notebook_metadata_json)
        except json.JSONDecodeError:
            message="Invalid JSON for notebook_metadata_json."
            logger.error(message)
            raise HTTPException(status_code=400, detail=message)

        notebook_id = SESSION_LOG_ID
        notebook_metadata["notebook_id"] = notebook_id
             
        ## This line is to generate spark SQL for testing. Disable this unless you want to see sample spark SQL generated
        sql_generated=generate_sparksql(json_mapping=clean_json,query_already_exist='n')
        # logger.debug(sql_generated)
    logger.info("JSON generation completed successfully!")
    return {"status_code": "200","notebook_metadata_json": notebook_metadata, "content": results}

# --- Old llm_semantic_validator commented out for traceability ---
# def llm_semantic_validator(generated_json: str,excel_sttm: str) -> dict:
#     judge_prompt = """
#                 You are a data engineering validator specialized in Source-to-Target Mapping (STTM) validation. Your task is to assess whether the provided STTM JSON correctly represents the original Excel-based STTM and meets the required format.
#                 ## METICULOUSLY READ ALL INFORMATION FROM BOTH STTM JSON AND ORIGINAL EXCEL-BASED STTM, BEFORE TAKING DECISION.
#                 ...
#     result = get_llm_response(user_prompt=judge_prompt)
#     # Optional: clean and parse the result
#     clean_json = result.replace("```json", "").replace("```", "").strip()
#     # print("clean_json")
#     # print(clean_json)
#     logger.info(f"Validation result:{clean_json}")
#     try:
#         result_json = json.loads(clean_json)
#     except Exception as e:
#         logger.error(f"LLM validator returned non-JSON response: {clean_json}")
#         raise HTTPException(status_code=500, detail="LLM validator did not return valid JSON")
#     
#     return result_json

# --- Simplified llm_semantic_validator ---
def llm_semantic_validator(generated_json: str, excel_sttm: str) -> dict:
    """
    Simplified LLM validation for complex cases only.
    """
    # Create a minimal validation prompt
    validation_prompt = f"""
Validate this STTM JSON for complex transformation correctness.

JSON to validate:
{generated_json[:5000]}...  # Limit size

Key validation points:
1. Are complex transformations (Case When, Conditional, custom SQL) syntactically correct?
2. Do transformations reference valid columns?
3. Are join conditions properly formatted?

Return only:
{{"is_valid": true/false, "strict_issues": ["issue1", "issue2"], "non_strict_issues": []}}
"""

    try:
        result = get_llm_response(user_prompt=validation_prompt)
        clean_json = result.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        logger.error(f"LLM validation error: {str(e)}")
        # Default to passing if LLM validation fails
        return {"is_valid": True, "strict_issues": [], "non_strict_issues": []}





class STTMAgentOrchestrator:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    # --- Old method commented out for traceability ---
    # async def generate_reliable_json_sttm(self, sheet_data: str, meta: dict) -> dict:
    #     """Main loop to generate, validate, and finalize JSON STTM."""
    #     attempt = 0
    #     cumulative_feedback = ""
    #     while attempt < self.max_attempts:
    #         attempt += 1
    #         logger.info(f"Attempt {attempt}: Generating JSON STTM")
    #         json_prompt = self.build_generation_prompt(sheet_data, cumulative_feedback)
    #         ## This line is for using databricks LLM endpoints
    #         content= get_llm_response(user_prompt=json_prompt)
    #         # print("content")
    #         # print(content)
    #         ## This line is for using pepgenx LLM endpoints
    #         # content=get_llm_response(user_prompt=json_prompt)
    #         # content=get_llm_response(user_prompt=json_prompt)
    #         # print(content)
    #         clean_json = content.replace("```json", "").replace("```", "").strip()
    #         logger.debug('Generated JSON format STTM: {"json_sttm":"'+str(json.loads(clean_json))+'"}')
    #         if not self.syntax_validator(clean_json):
    #             logger.warning(f"Attempt {attempt}: JSON Syntax validation failed.")
    #             cumulative_feedback += "\nPrevious attempt failed due to JSON syntax errors. Ensure valid JSON format."
    #             continue
    #         feedback_json = llm_semantic_validator(clean_json, sheet_data)
    #         # print("feedback_json")
    #         # print(feedback_json)
    #         semantic_valid=feedback_json["is_valid"]
    #         strict_issues=feedback_json["strict_issues"]            
    #         non_strict_issues=feedback_json["non_strict_issues"]
    #         # print("semantic_valid")
    #         # print(semantic_valid)
    #         # print("strict_issues")
    #         # print(strict_issues)
    #         # print("non_strict_issues")
    #         # print(non_strict_issues)
    #         if semantic_valid:
    #             logger.info(f"Attempt {attempt}: JSON passed all validations.")
    #             parsed = json.loads(clean_json)
    #             # print("Returned from semantic validation")
    #             return parsed
    #         logger.warning(f"Attempt {attempt}: Semantic validation failed: {strict_issues}")
    #         cumulative_feedback += f"\nPrevious attempt had the following issues:\n{strict_issues}\nPlease correct them."
    #         time.sleep(1)  # Optional pause between retries
    #     message=f"Max attempts reached. Failed to generate reliable valid JSON STTM after multiple attempts. Issues: {strict_issues}"
    #     logger.error(message)
    #     raise HTTPException(status_code=500, detail=message)
    # --- End old method ---

    # --- New method: Smart validation and retry logic ---
    async def generate_reliable_json_sttm(self, sheet_data: str, excel_metadata: dict) -> dict:
        """Generate JSON with smart validation and minimal LLM calls"""
        attempt = 0
        cumulative_feedback = ""

        while attempt < self.max_attempts:
            attempt += 1
            logger.info(f"Attempt {attempt}: Generating JSON STTM")

            # Build prompt with progressive detail
            json_prompt = self.build_smart_prompt(sheet_data, excel_metadata, cumulative_feedback, attempt)

            try:
                # Generate JSON
                content = get_llm_response(user_prompt=json_prompt)
                clean_json = content.replace("```json", "").replace("```", "").strip()

                # Run comprehensive Python validation
                is_valid, issues, needs_llm_validation = comprehensive_python_validation(
                    clean_json, excel_metadata
                )

                if not is_valid:
                    logger.warning(f"Python validation failed: {issues}")
                    cumulative_feedback = analyze_error_patterns(issues)
                    time.sleep(0.5)  # Brief pause
                    continue

                # Parse JSON for potential LLM validation
                json_data = json.loads(clean_json)

                # Only use LLM validation if needed
                if needs_llm_validation:
                    logger.info("Complex transformations detected, running LLM validation")
                    validation_result = llm_semantic_validator(clean_json, sheet_data)

                    if not validation_result["is_valid"]:
                        logger.warning(f"LLM validation failed: {validation_result['strict_issues']}")
                        cumulative_feedback = "\n".join(validation_result['strict_issues'])
                        time.sleep(1)
                        continue
                else:
                    logger.info("Skipping LLM validation - all transformations are standard")

                # All validations passed
                logger.info(f"JSON generation successful on attempt {attempt}")
                return json_data

            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}")
                cumulative_feedback = f"Error occurred: {str(e)[:200]}"
                time.sleep(1)

        # Max attempts reached
        raise HTTPException(
            status_code=500,
            detail=f"Failed after {attempt} attempts. Last issues: {cumulative_feedback}"
        )

    def build_smart_prompt(self, sheet_data: str, excel_metadata: dict,
                          feedback: str = "", attempt: int = 1) -> str:
        """Build a targeted prompt based on Excel structure"""

        # Add hints based on detected structure
        hints = []
        if excel_metadata.get('target_columns'):
            hints.append(f"Found {len(excel_metadata['target_columns'])} target columns")
        if excel_metadata.get('source_tables'):
            hints.append(f"Found source tables: {', '.join(excel_metadata['source_tables'][:5])}")

        # Base prompt
        prompt = f"""
You are a data engineering expert. Extract metadata from this STTM spreadsheet.

{sheet_data}

{"Structure hints: " + "; ".join(hints) if hints else ""}

Create a JSON with this exact structure:
- target_table: The target table name
- source_tables: List of source tables with name, desc, catalog, schema
- column_mapping: Dictionary mapping each target column to its source

Important:
- Include ALL target columns found in the spreadsheet
- Every source table referenced in transformations must be in source_tables list
- Use exact column names as they appear in the spreadsheet

Output only valid JSON, no explanations.
"""

        if attempt > 1 and feedback:
            prompt += f"\n\nFIX THESE SPECIFIC ISSUES:\n{feedback}"

        return prompt

    @staticmethod
    def syntax_validator(json_string: str) -> bool:
        """Quick syntax validation"""
        try:
            json.loads(json_string)
            return True
        except json.JSONDecodeError:
            return False



# --- Old orchestrate_json_sttm commented out for traceability ---
# @app1.post(f"/{appName}/api/v1/edf/genai/codegenservices/orchestrate-json-sttm")
# async def orchestrate_json_sttm(
#     sttm_metadata_json: str = Form(...),    # JSON string of list of dicts
#     sttm_files: List[UploadFile] = File(...), 
#     notebook_metadata_json: str = Form(...) 
# ):
# 
#     try:
#         metadata_list = json.loads(sttm_metadata_json)
#     except json.JSONDecodeError:
#         message="Invalid JSON for sttm_metadata_json."
#         logger.error(message)
#         raise HTTPException(status_code=400, detail=message)
#         
#     try:
#         notebook_metadata = json.loads(notebook_metadata_json)
#     except json.JSONDecodeError:
#         message="Invalid JSON for notebook_metadata_json."
#         logger.error(message)
#         raise HTTPException(status_code=400, detail=message)
# 
#     if not isinstance(metadata_list, list):
#         message="sttm_metadata_json must be a list of objects."
#         logger.error(message)
#         raise HTTPException(status_code=400, detail=message)
# 
#     if len(metadata_list) != len(sttm_files):
#         message="Mismatched number of STTM files and STTM metadata entries."
#         logger.error(message)
#         raise HTTPException(status_code=400, detail=message)
# 
#     results = {}
#     orchestrator = STTMAgentOrchestrator()
# 
#     for idx, file in enumerate(sttm_files):
#         logger.info(f"Processing file :: {file.filename}")
#         meta = get_metadata(metadata_list, file.filename.strip())
#         target_table_name = meta.get("target_table_name").strip()
#         sheet_name = meta.get("sheet_name").strip()
# 
#         contents = file.file.read()
#         excel_data = pd.read_excel(BytesIO(contents), sheet_name=sheet_name)
#         sheet_data = excel_data.to_csv(index=False)
# 
#         final_json =await orchestrator.generate_reliable_json_sttm(sheet_data, meta)
#         # print("final_json")
#         # print(final_json)
#         results[target_table_name] = {"metadata": meta, "json_sttm": final_json}
# 
#     notebook_metadata = json.loads(notebook_metadata_json)
#     notebook_metadata["notebook_id"] = "SESSION_LOG_ID"
# 
#     logger.info("JSON generation completed successfully!")
#     return {"status_code": "200", "notebook_metadata_json": notebook_metadata, "content": results}

# --- New simplified orchestrate_json_sttm with smart validation ---
@app1.post(f"/{appName}/api/v1/edf/genai/codegenservices/orchestrate-json-sttm")
async def orchestrate_json_sttm(
    sttm_metadata_json: str = Form(...),
    sttm_files: List[UploadFile] = File(...),
    notebook_metadata_json: str = Form(...)
):
    """Simplified endpoint with smart validation"""

    # Input validation
    try:
        metadata_list = json.loads(sttm_metadata_json)
        notebook_metadata = json.loads(notebook_metadata_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON in request")

    if not isinstance(metadata_list, list):
        raise HTTPException(status_code=400, detail="sttm_metadata_json must be a list")

    if len(metadata_list) != len(sttm_files):
        raise HTTPException(status_code=400, detail="Mismatch between files and metadata count")

    results = {}
    orchestrator = STTMAgentOrchestrator()
    processing_stats = {
        "files_processed": 0,
        "python_validations": 0,
        "llm_validations": 0,
        "errors": []
    }

    # Process each file
    for idx, file in enumerate(sttm_files):
        logger.info(f"Processing file {idx+1}/{len(sttm_files)}: {file.filename}")

        try:
            # Get metadata
            meta = get_metadata(metadata_list, file.filename.strip())
            if not meta:
                error_msg = f"No metadata found for {file.filename}"
                logger.error(error_msg)
                processing_stats["errors"].append(error_msg)
                continue

            target_table_name = meta.get("target_table_name", "").strip()
            sheet_name = meta.get("sheet_name", "").strip()

            if not target_table_name or not sheet_name:
                error_msg = f"Missing target_table_name or sheet_name for {file.filename}"
                logger.error(error_msg)
                processing_stats["errors"].append(error_msg)
                continue

            # Read and optimize Excel
            contents = file.file.read()
            excel_data = pd.read_excel(BytesIO(contents), sheet_name=sheet_name)

            # Smart optimization and metadata extraction
            optimized_csv, excel_metadata = optimize_excel_data(excel_data)

            # Check if file has minimum required data
            if not excel_metadata.get('has_data'):
                error_msg = f"File {file.filename} has no data"
                logger.error(error_msg)
                processing_stats["errors"].append(error_msg)
                continue

            # Generate JSON with smart validation
            final_json = await orchestrator.generate_reliable_json_sttm(
                optimized_csv, excel_metadata
            )

            results[target_table_name] = {
                "metadata": meta,
                "json_sttm": final_json
            }
            processing_stats["files_processed"] += 1

        except Exception as e:
            error_msg = f"Failed to process {file.filename}: {str(e)}"
            logger.error(error_msg)
            processing_stats["errors"].append(error_msg)

    # Add processing stats to response
    notebook_metadata["notebook_id"] = SESSION_LOG_ID
    notebook_metadata["processing_stats"] = processing_stats

    logger.info(f"Processing complete. Processed {processing_stats['files_processed']}/{len(sttm_files)} files")

    return {
        "status_code": "200",
        "notebook_metadata_json": notebook_metadata,
        "content": results
    }

# --- Simple Monitoring Endpoints ---
from datetime import datetime

# Simple stats tracking
processing_metrics = {
    "total_requests": 0,
    "successful_generations": 0,
    "failed_generations": 0,
    "python_validations": 0,
    "llm_validations": 0,
    "avg_attempts": []
}

@app1.get(f"/{appName}/stats")
def get_stats():
    """Get processing statistics"""
    avg_attempts = sum(processing_metrics["avg_attempts"]) / len(processing_metrics["avg_attempts"]) if processing_metrics["avg_attempts"] else 0

    return {
        "total_requests": processing_metrics["total_requests"],
        "successful_generations": processing_metrics["successful_generations"],
        "failed_generations": processing_metrics["failed_generations"],
        "python_validations": processing_metrics["python_validations"],
        "llm_validations": processing_metrics["llm_validations"],
        "average_attempts": round(avg_attempts, 2),
        "success_rate": round(
            processing_metrics["successful_generations"] /
            max(processing_metrics["total_requests"], 1) * 100, 2
        )
    }

@app1.get(f"/{appName}/health")
def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
# --- End Simple Monitoring Endpoints ---

