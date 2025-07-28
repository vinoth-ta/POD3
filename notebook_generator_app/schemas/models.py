from pydantic import BaseModel
from typing import List, Dict, Any, Union, TypedDict, Optional


# Pydantic validation models
class MetaInfo(BaseModel):
    user_id: str
    table_load_type: str
    domain: str
    product: str    
    notebook_name: str
    notebook_id: str

class DataInfo(BaseModel):
    metadata: Dict[str, Any]
    json_sttm: Dict[str, Any]

class PromptRequestModel(BaseModel):
    status_code: str
    notebook_metadata_json: MetaInfo
    content: Dict[str, DataInfo]

class PromptResponseModel(BaseModel):
    success: bool = True
    message: str
    notebook_id: str
    notebook_name: str
    data: str

class ServerError(BaseModel):
    error_code: int
    error_message: str

class ValidationError(BaseModel):
    loc: List[Union[str, int]]
    msg: str
    type: str

class HTTPValidationError(BaseModel):
    detail: List[ValidationError]

class SQLGenerationFailure(BaseModel):
    error_code: str
    error_message: str
    failure_reason: str
    retries: int

class SQLState(TypedDict):
    sttm: dict
    instructions: Optional[str]
    sql: Optional[str]
    reviewed_sql: Optional[str]
    retry_count: int
    validation_result: str
    validation_failure_reason: str
    previous_generated_sql: str
    failure_context: str
    layer_classification: Optional[str]
    multisilver_flag: bool
    domain: Optional[str]
    product: Optional[str]
    logic_args: Dict[str, Any]