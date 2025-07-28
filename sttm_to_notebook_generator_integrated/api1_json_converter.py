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
        ## This line is for using databricks LLM endpoints
        spark_sql_query=get_databricks_endpoint_response(user_prompt=query_prompt,max_tokens=80000,generation_model='databricks-claude-3-7-sonnet')
        
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
        # Use Azure OpenAI instead of Databricks/PepGenX
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key="4feeebf652bd46168c6a863b99314fc9",
            api_version="2024-07-01-preview",
            azure_endpoint="https://tigeropenaiservice.openai.azure.com/",
        )
        
        deployment_name = "gpt-4o"
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a data engineering expert specializing in Source-to-Target Mapping (STTM) analysis and JSON generation."},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=16384
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Azure OpenAI LLM invocation failed with error : {str(e)}")
        raise HTTPException(status_code=502, detail="LLM call failed!")
      
def get_metadata(metadata_list, file_name):
    for idx, meta_dict in enumerate(metadata_list):
        file_name_from_meta = meta_dict.get("file_name")
        if file_name_from_meta and file_name_from_meta.strip() == file_name:
            return meta_dict
    meta_dict={}
    return meta_dict

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
        
        target_table_name = meta.get("target_table_name", "").strip()
        sheet_name = meta.get("sheet_name", "").strip()


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
                    
                    CRITICAL HANDLING OF MISSING SOURCE DETAILS:
                    	MANDATORY: Include ALL target columns from the Excel STTM in the JSON output, even if source details are missing
                    	For columns with missing source details (source_table, source_field, source_datatype, source_desc are empty/NaN):
                    	If the transformation contains "Default Value" or a numeric/text value, treat it as a hardcoded default value
                    	If the transformation contains "ETL Audit Column", use the most common source table from other rows as the source_table
                    	For audit columns (XTNDFSystemId, XTNDFReportingUnitId, XTNCreatedTime, XTNCreatedById, XTNUpdatedTime, XTNUpdatedById):
                    	Use the primary source table (usually the first one mentioned in the STTM) as source_table
                    	Use the target column name as source_field
                    	Use the target datatype as source_datatype
                    	Use "Audit column from source system" as source_desc
                    	For any column with missing source details, use empty strings ("") for missing fields but still include the column
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
                    5.	For missing source details, make reasonable assumptions based on the context and other rows in the STTM.
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
                    Example: Conditional("price > 100", "High", "Low")
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

def llm_semantic_validator(generated_json: str,excel_sttm: str) -> dict:
    judge_prompt = """
                You are a data engineering validator specialized in Source-to-Target Mapping (STTM) validation. Your task is to assess whether the provided STTM JSON correctly represents the original Excel-based STTM and meets the required format.
                
                **ULTRA-LENIENT VALIDATION RULE**: Be extremely lenient. Only mark issues as "strict" if the JSON is completely unusable (missing target table name, invalid JSON structure). ALL other issues (missing columns, missing source details, missing source tables) should be "non-strict" issues.
                
                ## METICULOUSLY READ ALL INFORMATION FROM BOTH STTM JSON AND ORIGINAL EXCEL-BASED STTM, BEFORE TAKING DECISION.

				Please analyze the following:
				1. The original Excel-based STTM data
				2. The generated STTM JSON that needs validation
				3. A sample approved STTM JSON that serves as the reference format

				**CRITICAL VALIDATION REQUIREMENTS:**
				-------------------------------------
				1. **HIGHEST PRIORITY**: Verify the JSON has valid syntax without parsing errors
				2. **HIGHEST PRIORITY**: Confirm target_table is properly specified
				3. **CHECK**: Ensure target columns from the Excel STTM are included in the JSON column_mapping (but missing columns are non-strict issues)
				4. **CHECK**: Check that source tables referenced in transformations are included in source_tables (but missing tables are non-strict issues)

				REMEMBER: Only missing target table name and invalid JSON structure make the STTM completely unusable!

				Additional validation instructions:
				1. Validate the structural integrity of the generated JSON:
				   - Check that it's valid JSON syntax without parsing errors (CRITICAL)
				   - Verify all required top-level keys are present (target_table, workflow_logic, parameters, source_tables, column_mapping)
				   - Ensure nested structures match the approved format

				2. Cross-check Excel STTM with JSON STTM:
				   - **CHECK**: Identify all target columns mentioned in the Excel STTM
				   - **CHECK**: Verify each of these target columns exists in the JSON column_mapping section (missing columns are non-strict issues)
				   - Check if source tables mentioned in Excel are all represented in the JSON source_tables section (missing tables are non-strict issues)
				   - Verify that transformations described in Excel are properly captured in the JSON

				3. Validate completeness of content:
				   - Confirm target_table is properly specified (CRITICAL)
				   - Verify source_tables contains all necessary tables with their metadata (name, desc, catalog, schema)
				   - Check that column_mapping includes entries for all target columns (missing columns are non-strict issues)
				   - Ensure each column mapping contains required fields (target_datatype, target_desc, sources)
				   - Verify that sources contains necessary fields (source_table, source_field, source_datatype, source_desc, transformation)
				   - Confirm that standard coded transformations include their explanations in parentheses

				4. Compare with the approved STTM:
				   - Check that the structure and organization matches the approved format
				   - Verify the level of detail is consistent with the approved example
				   - Confirm that transformation explanations follow the same pattern

				5. Classify issues into two categories:
				   - **Strict issues**: Critical problems that make the STTM unusable, such as:
					 * Missing target table name
					 * Invalid JSON structure
					 * Completely malformed JSON that cannot be parsed
					 
				   **CRITICAL NOTE**: Missing columns, missing source details, missing source tables, or any other completeness issues should be treated as non-strict issues, NOT strict issues. Only truly critical structural problems (missing target table name, invalid JSON) should be strict issues.
					 
				   - Non-strict issues: Minor problems that don't invalidate the STTM but should be improved:
					 * Missing descriptions
					 * Missing data types
					 * Incomplete parameter information
					 * Missing catalog/schema information
					 * Missing explanations for standard transformations
					 * Inconsistent formatting
					 * Missing catalog and schema information of source or target tables
					 * Missing or partial transformation rules
					 * **Missing source details for audit columns (XTN*) - these can be inferred**
					 * **Missing source details for default value columns - these are acceptable**
					 * **Missing source details for ETL audit columns - these can be inferred**

				**IMPORTANT**: Do not evaluate the logical correctness of the transformations themselves - focus ONLY on format, structure, and completeness of information.
				
				**SPECIAL HANDLING FOR AUDIT COLUMNS**: 
				- For audit columns (XTNDFSystemId, XTNDFReportingUnitId, XTNCreatedTime, XTNCreatedById, XTNUpdatedTime, XTNUpdatedById), missing source details are acceptable and should be treated as non-strict issues
				- For default value columns, missing source details are acceptable as long as the transformation rule is present
				- For ETL audit columns, missing source details are acceptable and can be inferred from context
				
				**MISSING COLUMNS HANDLING**:
				- Missing target columns from Excel in the JSON should be treated as non-strict issues, NOT strict issues
				- Missing source tables should be treated as non-strict issues, NOT strict issues
				- Any completeness issues should be non-strict, not strict

				6. Provide your validation report strictly in the following JSON format and nothing more than this JSON:
				```
                    {
                      "is_valid": true or false,
                      "strict_issues": [
                        "Description of strict issue 1",
                        "Description of strict issue 2"
                      ],
                      "non_strict_issues": [
                        "Description of non-strict issue 1",
                        "Description of non-strict issue 2"
                      ]
                    }```
                    
					Original Excel-based STTM:
					"""+excel_sttm+"""

                    Generated STTM JSON to validate:
                    ```"""+generated_json+"""```

                    Approved STTM JSON format reference:
                    ```
                    {
                        "target_table": "XTNBusinessTravelTaxDetail",
                        "workflow_logic": "",
                        "parameters": {},
                        "source_tables": [
                            {
                                "name": "tbl_SNT_SUPP_globalgbttvltax",
                                "desc": "Global business travel tax details",
                                "catalog": "",
                                "schema": "fdn_procurement_confidential_bronze"
                            }
                        ],
                        "column_mapping": {
                            "SystemId": {
                                "target_datatype": "INT",
                                "target_desc": "A PepsiCo-assigned numerical identifier for a unique source system within PepsiCo's system landscape.",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "Default Value: 420 (Uses the hardcoded value 420)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "BusinessTravelInvoiceUniqueId": {
                                "target_datatype": "STRING",
                                "target_desc": "A numeric identifier that preserves the uniqueness of each passenger on the invoice, especially if there is more than one passenger. For example, 1 = Passenger 1, 2 = Passenger 2. This ensures accurate passenger tracking.",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "Concatenate(BusinessTravelAgencyUniqueId,\"|\",TravelAgencyAccountingBranchCode,\"|\",TravelInvoiceId,\"|\",TravelInvoiceLineId) (Joins multiple columns together with the '|' delimiter)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "BusinessTravelTaxDetailUniqueId": {
                                "target_datatype": "STRING",
                                "target_desc": "An unique identifier that preserves the uniqueness of each user tax detail.",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "Substring_col(\"BusinessTravelInvoiceUniqueId\", 1, 3) (Extracts a substring from BusinessTravelInvoiceUniqueId starting at position 1 with length 3)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "TravelInvoiceDate": {
                                "target_datatype": "DATE",
                                "target_desc": "The date when the travel agency or vendor issues the invoice to the passenger; formatted as YYMMDD. This value is crucial for tracking billing and payment timelines.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXIDTE",
                                    "source_datatype": "STRING",
                                    "source_desc": "The date when the travel agency or vendor issues the invoice to the passenger; formatted as YYMMDD. This value is crucial for tracking billing and payment timelines.",
                                    "transformation": "DateCalculation(-20) (Subtracts 20 days from the date)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "BusinessTravelAgencyUniqueId": {
                                "target_datatype": "STRING",
                                "target_desc": "A unique alphanumeric identifier assigned to each machine or system used within the AMEX GBT (Global Business Travel) network. This code helps in distinguishing between different machines or systems in the database.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXMCID",
                                    "source_datatype": "STRING",
                                    "source_desc": "A unique alphanumeric identifier assigned to each machine or system used within the AMEX GBT (Global Business Travel) network. This code helps in distinguishing between different machines or systems in the database.",
                                    "transformation": "TitleCase (Capitalizes first letter of each word)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "TravelAgencyAccountingBranchCode": {
                                "target_datatype": "STRING",
                                "target_desc": "The branch number of the travel agency where the transaction appears for accounting settlement. This value is essential for financial reconciliation and reporting.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXACBR",
                                    "source_datatype": "STRING",
                                    "source_desc": "The branch number of the travel agency where the transaction appears for accounting settlement. This value is essential for financial reconciliation and reporting.",
                                    "transformation": "Substring(1, 2) (Extracts substring starting from position 1 with length 2)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "TravelInvoiceId": {
                                "target_datatype": "STRING",
                                "target_desc": "A unique alphanumeric code that is generated and assigned by the Back Office system when it processes the booking information received from the CRS (Computer Reservation System) interface. This value helps in tracking and referencing specific transactions.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXINV",
                                    "source_datatype": "STRING",
                                    "source_desc": "A unique alphanumeric code that is generated and assigned by the Back Office system when it processes the booking information received from the CRS (Computer Reservation System) interface. This value helps in tracking and referencing specific transactions.",
                                    "transformation": "DateExtraction(\"TravelInvoiceDate\", \"yyyy\") (Extracts the year component from TravelInvoiceDate)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "TravelInvoiceLineId": {
                                "target_datatype": "STRING",
                                "target_desc": "A numeric identifier that preserves the uniqueness of each passenger on the invoice, especially if there is more than one passenger. For example, 1 = Passenger 1, 2 = Passenger 2. This ensures accurate passenger tracking.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXNPAS",
                                    "source_datatype": "STRING",
                                    "source_desc": "A numeric identifier that preserves the uniqueness of each passenger on the invoice, especially if there is more than one passenger. For example, 1 = Passenger 1, 2 = Passenger 2. This ensures accurate passenger tracking.",
                                    "transformation": "Trim (Removes leading and trailing whitespace)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "TaxDetailLineId": {
                                "target_datatype": "STRING",
                                "target_desc": "Several taxes may apply to one invoice and carry numerical sequence to preserve uniqueness.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXSEQN",
                                    "source_datatype": "STRING",
                                    "source_desc": "Several taxes may apply to one invoice and carry numerical sequence to preserve uniqueness.",
                                    "transformation": "trimtrailingzeros(\"TXSEQN\") (Removes trailing zeros)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "TaxCode": {
                                "target_datatype": "STRING",
                                "target_desc": "Represents a specific tax use case and is utilized for calculating the correct tax amounts based on information such as country, tax type, tax rate type, and, in some cases, tax deductibility.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXCODE",
                                    "source_datatype": "STRING",
                                    "source_desc": "Represents a specific tax use case and is utilized for calculating the correct tax amounts based on information such as country, tax type, tax rate type, and, in some cases, tax deductibility.",
                                    "transformation": "replace(\"**\", \"US1\") (Replaces '**' with 'US1')",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "TaxAmount": {
                                "target_datatype": "DECIMAL(18,2)",
                                "target_desc": "Amount of this tax. Amount field is provided in the consolidated currency designated at extract and agreed upon by client. If the transaction currency code is different that the designated extract currency the amounts are converted. IF the currency code for a transaction matches the extract currency the amounts are not converted.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXAMT",
                                    "source_datatype": "STRING",
                                    "source_desc": "Amount of this tax. Amount field is provided in the consolidated currency designated at extract and agreed upon by client. If the transaction currency code is different that the designated extract currency the amounts are converted. IF the currency code for a transaction matches the extract currency the amounts are not converted.",
                                    "transformation": "Direct (Directly maps TXAMT to TaxAmount with casting to target type)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "OriginalCurrencyCode": {
                                "target_datatype": "STRING",
                                "target_desc": "Code for currency used in billing, such as: USD, GBP, SGD",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXOCUR",
                                    "source_datatype": "STRING",
                                    "source_desc": "Code for currency used in billing, such as: USD, GBP, SGD.",
                                    "transformation": "trimleadingzeros(\"TXOCUR\") (Removes leading zeros)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "CurrencyCode": {
                                "target_datatype": "STRING",
                                "target_desc": "Code for extracted currency, such as: USD, GBP, SGD. This currency code is used in currency conversion based on the exchange rate on invoice date.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXCCUR",
                                    "source_datatype": "STRING",
                                    "source_desc": "Code for extracted currency, such as: USD, GBP, SGD. This currency code is used in currency conversion based on the exchange rate on invoice date.",
                                    "transformation": "Conditional(\"TXAMT > 1000\", \"US\", \"IND\") (IF-ELSE style logic: if TXAMT > 1000 then 'US' else 'IND')",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "MaximumTransactionNumberValue": {
                                "target_datatype": "STRING",
                                "target_desc": "The maximum transaction number. This field is used for tracking and referencing transactions.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXTRNR",
                                    "source_datatype": "STRING",
                                    "source_desc": "The maximum transaction number. This field is used for tracking and referencing transactions.",
                                    "transformation": "Uppercase (Converts source string to uppercase)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "MaximumPassengerNumberValue": {
                                "target_datatype": "STRING",
                                "target_desc": "The maximum passenger number. This field is used for tracking and referencing passengers.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXMPAS",
                                    "source_datatype": "STRING",
                                    "source_desc": "The maximum passenger number. This field is used for tracking and referencing passengers.",
                                    "transformation": "Lowercase (Converts source string to lowercase)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "CompanyCode": {
                                "target_datatype": "STRING",
                                "target_desc": "It is an organizational unit within financial accounting and is part of the Finance Organization Structure. The PepsiCo Global Template design decision is that a Company Code generally has a one-to-one relationship with the legal entity.",
                                "sources": {
                                    "source_table": "tbl_SNT_SUPP_globalgbttvltax",
                                    "source_field": "TXFIL2",
                                    "source_datatype": "STRING",
                                    "source_desc": "The maximum passenger number. This field is used for tracking and referencing passengers.",
                                    "transformation": "NullHandling(\"TXFIL1\", \"TXFIL2\", \"PL\") (Replaces nulls with fallback values: tries TXFIL1 first, then TXFIL2, then uses 'PL' as default)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "XTNDFSystemId": {
                                "target_datatype": "INTEGER",
                                "target_desc": "A PepsiCo-assigned, 6-digit numerical identifier for a unique source system within the Enterprise Data Foundation. Usually, it is related to the System Identifier in that the last 3 digits are the same. It serves as primary key in the System Master table of the Data Foundation. ",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "Default Value: 1420 (Uses the hardcoded value 1420)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "XTNDFReportingUnitId": {
                                "target_datatype": "INTEGER",
                                "target_desc": "A PepsiCo-assigned numerical identifier for a reporting instance of an existing system within the Enterprise Data Foundation. It is the primary key in the Reporting Unit Master table of the Data Foundation. (A unique Reporting Unit indicates a specific country, internal/external type, plus source)",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "Default Value: 107019 (Uses the hardcoded value 107019)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "XTNCreatedTime": {
                                "target_datatype": "TIMESTAMP",
                                "target_desc": "Timestamp of when the record was created in the source system of record in YYYY-MM-DD HH:MM:SS:ff format.",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "ETL Audit Column (Populated by ETL process with creation timestamp)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "XTNCreatedById": {
                                "target_datatype": "STRING",
                                "target_desc": "A unique identifier associated to the user or job instance that created the record in the source system of record.",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "ETL Audit Column (Populated by ETL process with creator ID)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "XTNUpdatedTime": {
                                "target_datatype": "TIMESTAMP",
                                "target_desc": "Timestamp of when the record was updated in the source system of record in YYYY-MM-DD HH:MM:SS:ff format.",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "ETL Audit Column (Populated by ETL process with update timestamp)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            },
                            "XTNUpdatedById": {
                                "target_datatype": "STRING",
                                "target_desc": "A unique identifier associated to the user or job instance that last updated the record in the source system of record.",
                                "sources": {
                                    "source_table": "",
                                    "source_field": "",
                                    "source_datatype": "",
                                    "source_desc": "",
                                    "transformation": "ETL Audit Column (Populated by ETL process with updater ID)",
                                    "join_condition": "",
                                    "filter": ""
                                }
                            }
                        }
                    }
                    ```
                    """
    
    result = get_llm_response(user_prompt=judge_prompt)
    # Optional: clean and parse the result
    clean_json = result.replace("```json", "").replace("```", "").strip()
    # print("clean_json")
    # print(clean_json)
    logger.info(f"Validation result:{clean_json}")
    try:
        result_json = json.loads(clean_json)
    except Exception as e:
        logger.error(f"LLM validator returned non-JSON response: {clean_json}")
        raise HTTPException(status_code=500, detail="LLM validator did not return valid JSON")
    
    return result_json





class STTMAgentOrchestrator:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    async def generate_reliable_json_sttm(self, sheet_data: str, meta: dict) -> dict:
        """Main loop to generate, validate, and finalize JSON STTM."""
        attempt = 0
        cumulative_feedback = ""

        while attempt < self.max_attempts:
            attempt += 1
            logger.info(f"Attempt {attempt}: Generating JSON STTM")

            # Extract target table name from metadata
            target_table_name = meta.get("target_table_name", "").strip()
            
            json_prompt = self.build_generation_prompt(sheet_data, cumulative_feedback, target_table_name)

            ## This line is for using databricks LLM endpoints
            content= get_llm_response(user_prompt=json_prompt)
            # print("content")
            # print(content)
            
            ## This line is for using pepgenx LLM endpoints
            # content=get_llm_response(user_prompt=json_prompt)
            # content=get_llm_response(user_prompt=json_prompt)
            # print(content)

            clean_json = content.replace("```json", "").replace("```", "").strip()
            logger.debug('Generated JSON format STTM: {"json_sttm":"'+str(json.loads(clean_json))+'"}')

            if not self.syntax_validator(clean_json):
                logger.warning(f"Attempt {attempt}: JSON Syntax validation failed.")
                cumulative_feedback += "\nPrevious attempt failed due to JSON syntax errors. Ensure valid JSON format."
                continue

            feedback_json = llm_semantic_validator(clean_json, sheet_data)
            
            # print("feedback_json")
            # print(feedback_json)
            
            semantic_valid=feedback_json["is_valid"]
            strict_issues=feedback_json["strict_issues"]            
            non_strict_issues=feedback_json["non_strict_issues"]
            # print("semantic_valid")
            # print(semantic_valid)
            # print("strict_issues")
            # print(strict_issues)
            # print("non_strict_issues")
            # print(non_strict_issues)

            if semantic_valid:
                logger.info(f"Attempt {attempt}: JSON passed all validations.")
                parsed = json.loads(clean_json)
                # print("Returned from semantic validation")
                return parsed

            logger.warning(f"Attempt {attempt}: Semantic validation failed: {strict_issues}")
            cumulative_feedback += f"\nPrevious attempt had the following issues:\n{strict_issues}\nPlease correct them."
            
            time.sleep(1)  # Optional pause between retries

        message=f"Max attempts reached. Failed to generate reliable valid JSON STTM after multiple attempts. Issues: {strict_issues}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)


    @staticmethod
    def extract_target_columns(sheet_data: str) -> list:
        """Extract target column names from the CSV data."""
        try:
            lines = sheet_data.strip().split('\n')
            if len(lines) < 2:
                return []
            
            # Look for target column headers
            headers = lines[0].split(',')
            target_columns = []
            
            # Common target column header patterns
            target_patterns = ['target', 'Target', 'TARGET', 'target column', 'Target Column', 'TARGET COLUMN', 'Target Field', 'TARGET FIELD']
            
            for i, header in enumerate(headers):
                header_clean = header.strip().strip('"').strip("'")
                if any(pattern in header_clean for pattern in target_patterns):
                    # Extract target column names from this column
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split(',')
                            if i < len(parts):
                                col_name = parts[i].strip().strip('"').strip("'")
                                if col_name and col_name not in target_columns and col_name.lower() not in ['nan', 'none', '']:
                                    target_columns.append(col_name)
            
            # If no target columns found, try to extract from any column that might contain target field names
            if not target_columns:
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split(',')
                        for part in parts:
                            col_name = part.strip().strip('"').strip("'")
                            # Look for common target field patterns
                            if (col_name and 
                                col_name.lower() not in ['nan', 'none', ''] and
                                any(pattern in col_name for pattern in ['Id', 'ID', 'Name', 'Code', 'Type', 'Date', 'Time', 'XTN']) and
                                col_name not in target_columns):
                                target_columns.append(col_name)
            
            return target_columns
        except Exception as e:
            logger.warning(f"Failed to extract target columns: {e}")
            return []

    @staticmethod
    def build_generation_prompt(sheet_data: str, feedback: str = "", target_table_name: str = "") -> str:
        # Extract target columns from the data
        target_columns = STTMAgentOrchestrator.extract_target_columns(sheet_data)
        target_columns_str = ", ".join(target_columns) if target_columns else "None extracted"
        prompt = f"""
You are a data engineering expert specializing in Source-to-Target Mapping (STTM) analysis. Your task is to extract metadata from the provided STTM spreadsheet and generate a complete JSON structure.

STTM DATA:
{sheet_data}

TARGET TABLE NAME: {target_table_name}
EXTRACTED TARGET COLUMNS: {target_columns_str}

CRITICAL REQUIREMENTS:
1. **MANDATORY**: The target_table field MUST be "{target_table_name}" (exactly as provided)
2. **MANDATORY**: Include ALL target columns from the Excel STTM in the column_mapping section
3. **MANDATORY**: Never skip any column, even if source details are missing
4. **MANDATORY**: Use the exact JSON structure provided below
5. **MANDATORY**: If target columns were extracted above, ensure ALL of them are included in column_mapping

SOURCE TABLE EXTRACTION:
- Look for columns named "Source Table", "Bronze Table", "Source", or similar
- Extract all unique source table names
- For each source table, create an entry in source_tables array

COLUMN MAPPING RULES:
- For each target column in the Excel, create a corresponding entry in column_mapping
- If source details are missing, use empty strings ("") for source_table, source_field, source_datatype, source_desc
- For audit columns (XTNDFSystemId, XTNDFReportingUnitId, XTNCreatedTime, XTNCreatedById, XTNUpdatedTime, XTNUpdatedById):
  * Use the primary source table as source_table
  * Use the target column name as source_field
  * Use the target datatype as source_datatype
  * Use "Audit column from source system" as source_desc
- For "Default Value" transformations, extract the actual value
- For "ETL Audit Column", use appropriate source table and column names

WORKFLOW LOGIC:
- Look for sections titled "Overall Logic", "Functional Requirement", "Workflow Logic", or similar
- Extract the complete workflow description

PARAMETERS:
- Look for any variables or parameters mentioned in the STTM
- Create entries in the parameters object

EXACT JSON STRUCTURE TO FOLLOW:
{{
  "target_table": "{target_table_name}",
  "workflow_logic": "Extract the overall data load logic from the STTM",
  "parameters": {{
    "param1": "description of parameter 1",
    "param2": "description of parameter 2"
  }},
  "source_tables": [
    {{
      "name": "source_table_name",
      "desc": "source table description",
      "catalog": "catalog_name",
      "schema": "schema_name"
    }}
  ],
  "column_mapping": {{
    "TargetColumn1": {{
      "target_datatype": "STRING",
      "target_desc": "Target column description",
      "sources": {{
        "source_table": "source_table_name",
        "source_field": "source_column_name",
        "source_datatype": "STRING",
        "source_desc": "Source column description",
        "transformation": "Transformation logic with explanations",
        "join_condition": "Join condition if applicable",
        "filter": "Filter condition if applicable"
      }}
    }},
    "TargetColumn2": {{
      "target_datatype": "INTEGER",
      "target_desc": "Another target column description",
      "sources": {{
        "source_table": "",
        "source_field": "",
        "source_datatype": "",
        "source_desc": "",
        "transformation": "Default Value: 123",
        "join_condition": "",
        "filter": ""
      }}
    }}
  }}
}}

IMPORTANT NOTES:
- Use double quotes for all JSON keys and string values
- Include ALL target columns from the Excel, even if source details are missing
- For missing source details, use empty strings ("") but still include the column
- Ensure the JSON is syntactically valid
- Return ONLY the JSON string, no additional text or explanations

{f"PREVIOUS ATTEMPT FEEDBACK TO CORRECT:{chr(10)}{feedback}" if feedback and feedback.strip() else ""}
"""
        return prompt


    @staticmethod
    def syntax_validator(json_string: str) -> bool:
        try:
            json.loads(json_string)
            return True
        except json.JSONDecodeError:
            return False



@app1.post(f"/{appName}/api/v1/edf/genai/codegenservices/orchestrate-json-sttm")
async def orchestrate_json_sttm(
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
        
    try:
        notebook_metadata = json.loads(notebook_metadata_json)
    except json.JSONDecodeError:
        message="Invalid JSON for notebook_metadata_json."
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
    orchestrator = STTMAgentOrchestrator()

    for idx, file in enumerate(sttm_files):
        logger.info(f"Processing file :: {file.filename}")
        meta = get_metadata(metadata_list, file.filename.strip())
        target_table_name = meta.get("target_table_name", "").strip()
        sheet_name = meta.get("sheet_name", "").strip()

        contents = file.file.read()
        excel_data = pd.read_excel(BytesIO(contents), sheet_name=sheet_name)
        sheet_data = excel_data.to_csv(index=False)


        final_json =await orchestrator.generate_reliable_json_sttm(sheet_data, meta)
        # print("final_json")
        # print(final_json)
        
        # Use the target table name from the generated JSON if the metadata one is empty
        if not target_table_name and final_json.get("target_table"):
            target_table_name = final_json["target_table"]
        elif not target_table_name:
            target_table_name = f"table_{idx}"  # Fallback to indexed name
            
        # Add target_table_name to metadata for API2 compatibility
        meta_with_target = meta.copy()
        meta_with_target["target_table_name"] = target_table_name
        
        results[target_table_name] = {"metadata": meta_with_target, "json_sttm": final_json}

    notebook_metadata = json.loads(notebook_metadata_json)
    notebook_metadata["notebook_id"] = "SESSION_LOG_ID"

    logger.info("JSON generation completed successfully!")
    return {"status_code": "200", "notebook_metadata_json": notebook_metadata, "content": results}

