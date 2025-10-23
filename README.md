# STTM-to-Notebook Generator v1.1.0

Advanced system that converts Source-to-Target Mapping (STTM) Excel files into complete Databricks ETL notebooks using Gen AI with LLM integration.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Usage](#api-usage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Architecture](#architecture)

---

## Prerequisites

Before setting up the project, ensure you have:

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Azure OpenAI API access (or other LLM provider)
- Virtual environment support

---

## Local Setup

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd POD3
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory with the following configuration:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-deployment-name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_API_KEY=your_api_key_here

# Alternative configuration names (legacy support)
endpoint=https://your-endpoint.openai.azure.com/
deployment=gpt-4-deployment-name
api_version=2024-12-01-preview
subscription_key=your_api_key_here
model_name=gpt-4

# Application Configuration
ROOTCONTEXT=silver-codegen-genai
```

**Note:** Replace the placeholder values with your actual Azure OpenAI credentials.

### Step 5: Verify Setup

```bash
python test_setup.py
```

This will verify that all dependencies are installed and configuration is correct.

---

## Configuration

### Azure OpenAI Settings

The application uses Azure OpenAI with the following configuration:

- **Model**: GPT-4
- **Max Tokens**: 4096 (adjusted for model compatibility)
- **Temperature**: 0.1 (for consistent outputs)
- **API Version**: 2024-12-01-preview

### Template System

Templates for notebook generation are located in the `templates/` directory:

- `templates/silver/` - Silver layer ETL templates
- `templates/gold/` - Gold layer ETL templates

You can customize templates for specific domains and products by creating subdirectories:
```
templates/silver/<domain>/<product>/
```

---

## Running the Application

### Start the API Server

```bash
uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8000
```

The application will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Alternative: Using Python Script

```bash
python run_app.py
```

---

## API Usage

### Available Endpoints

#### 1. JSON Conversion Only
**Endpoint:** `POST /None/api/v1/edf/genai/codegenservices/orchestrate-json-sttm`

Converts STTM Excel files to structured JSON mapping.

#### 2. Full Pipeline (Recommended)
**Endpoint:** `POST /None/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook`

Converts STTM to JSON AND generates complete Databricks notebook.

### Request Format

**Content-Type:** `multipart/form-data`

**Required Fields:**

1. **sttm_files** (file): STTM Excel file(s)
2. **sttm_metadata_json** (string): JSON metadata for STTM files
3. **notebook_metadata_json** (string): JSON metadata for notebook generation

### Example Request

#### Using Swagger UI (Recommended)

1. Navigate to http://localhost:8000/docs
2. Find the endpoint: `/None/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook`
3. Click "Try it out"
4. Fill in the required fields:

**sttm_metadata_json:**
```json
[
  {
    "file_name": "YourFile.xlsx",
    "sheet_name": "Sheet1",
    "target_table_name": "your_target_table"
  }
]
```

**notebook_metadata_json:**
```json
{
  "user_id": "your_user_id",
  "table_load_type": "silver",
  "domain": "finance",
  "product": "analytics",
  "notebook_name": "your_notebook_name"
}
```

**Important:** `table_load_type` must be either `"silver"` or `"gold"` to match available templates.

5. Upload your STTM Excel file
6. Click "Execute"

#### Using cURL

```bash
curl -X POST "http://localhost:8000/None/api/v1/edf/genai/codegenservices/from-sttm-generate-notebook" \
  -H "Content-Type: multipart/form-data" \
  -F "sttm_files=@path/to/your_file.xlsx" \
  -F 'sttm_metadata_json=[{"file_name":"your_file.xlsx","sheet_name":"Sheet1","target_table_name":"target_table"}]' \
  -F 'notebook_metadata_json={"user_id":"user123","table_load_type":"silver","domain":"finance","product":"analytics","notebook_name":"test_notebook"}'
```

### Response Format

```json
{
  "success": true,
  "message": "Notebook generated successfully.",
  "notebook_id": "unique-id",
  "notebook_name": "generated_notebook.py",
  "data": "# Databricks notebook source\n# Generated ETL code..."
}
```

The `data` field contains the complete Databricks notebook code.

---

## Testing

### Run Setup Verification

```bash
python test_setup.py
```

### Manual Testing

1. Start the server
2. Open Swagger UI at http://localhost:8000/docs
3. Use the interactive interface to test endpoints
4. Check server logs for detailed processing information

### Automated Tests

```bash
# Run comparison tests
python tests/automated/test_comparison.py

# Run manual tests
python tests/manual/manual_test_comparison.py
```

---

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8001
```

### Module Not Found Errors

Ensure virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Template Not Found Error

If you see: `[Errno 2] No such file or directory: '.../templates/incremental/...'`

**Solution:** Use `"silver"` or `"gold"` for `table_load_type` instead of `"incremental"`.

### LLM API Errors

#### Error: "max_tokens is too large"

This has been fixed. The application now uses 4096 tokens (compatible with GPT-4).

#### Error: "502: LLM call failed"

Check:
1. Azure OpenAI credentials in `.env` are correct
2. API endpoint is accessible
3. Deployment name matches your Azure configuration
4. API key is valid and has sufficient quota

#### Error: "401 Unauthorized"

Verify your `AZURE_OPENAI_API_KEY` in the `.env` file.

### Import Errors

If you encounter import errors:

```bash
# Ensure you're in the project root
cd /Users/vinothpremkumar/Documents/POD-3/POD3

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

---

## Project Structure

```
POD3/
├── README.md                                      # This file
├── requirements.txt                               # Python dependencies
├── .env                                          # Environment configuration
├── .gitignore                                    # Git ignore rules
├── Dockerfile                                    # Docker configuration
├── docker-compose.yml                            # Docker Compose setup
├── run_app.py                                    # Application entry point
├── test_setup.py                                 # Setup verification script
│
├── sttm_to_notebook_generator_integrated/        # Main application
│   ├── api1_json_converter_optimized.py         # STTM to JSON converter (v1.1.0)
│   ├── api3_sttm_to_notebook_generator.py       # Main API orchestrator
│   ├── read_env_var.py                          # Environment configuration
│   └── log_handler.py                           # Logging utilities
│
├── notebook_generator_app/                       # Notebook generation module
│   ├── main.py                                  # Notebook generation API
│   ├── llm/                                     # LLM integration
│   │   └── langchain_workflow.py                # LangGraph workflow
│   ├── schemas/                                 # Data models
│   │   └── models.py                            # Pydantic models
│   └── utilities/                               # Helper functions
│       └── helpers.py                           # Utility functions
│
├── templates/                                    # Jinja2 templates
│   ├── silver/                                  # Silver layer templates
│   │   ├── instructions_langchain.txt
│   │   ├── silver_notebook_template.j2
│   │   └── system_prompt.txt
│   └── gold/                                    # Gold layer templates
│       ├── instructions_langchain.txt
│       ├── gold_notebook_template.j2
│       └── system_prompt.txt
│
├── tests/                                        # Testing
│   ├── automated/                               # Automated tests
│   ├── manual/                                  # Manual tests
│   └── results/                                 # Test outputs
│
├── data/                                         # Sample data
│   └── sample_sttm/                             # Sample STTM files
│
├── scripts/                                      # Utility scripts
│   ├── analysis/                                # Analysis tools
│   └── setup/                                   # Setup scripts
│
├── logs/                                         # Application logs
└── venv/                                         # Virtual environment
```

---

## Architecture

### System Components

1. **API1 - JSON Converter** (`api1_json_converter_optimized.py`)
   - Parses STTM Excel files
   - Extracts source-to-target mappings
   - Generates structured JSON using LLM
   - Validates transformations

2. **API2 - Notebook Generator** (`notebook_generator_app/main.py`)
   - Takes JSON mapping as input
   - Uses LangGraph multi-agent workflow
   - Generates Databricks ETL code
   - Applies template-based rendering

3. **API3 - Orchestrator** (`api3_sttm_to_notebook_generator.py`)
   - Main FastAPI application
   - Coordinates API1 and API2
   - Handles full pipeline execution
   - Manages error handling and logging

### Processing Flow

```
Excel Upload → API1 → JSON Mapping → API2 → Databricks Notebook
```

1. User uploads STTM Excel file via Swagger UI
2. API1 converts Excel to structured JSON mapping
3. API2 generates Databricks notebook from JSON
4. Complete notebook code returned in API response

### Key Features

- Azure OpenAI Integration with GPT-4
- Smart validation and error recovery
- Multi-attempt generation with feedback loop
- Template-based code generation
- Comprehensive logging and monitoring
- Support for both Silver and Gold layer transformations
- Multi-table support
- Custom transformation handling

---

## Version History

### v1.1.0 (Current)
- Optimized STTM processor with enhanced performance
- Fixed max_tokens configuration for GPT-4 compatibility
- Smart validation and error recovery
- Multi-attempt JSON generation with feedback loop
- Improved Azure OpenAI integration
- Enhanced error handling and logging

### v1.0.0
- Initial release
- Basic STTM-to-Notebook pipeline
- Azure OpenAI integration
- Template system
- Error handling

---

## Support

For issues and questions:
- Check the Troubleshooting section above
- Review server logs in the terminal
- Create an issue in the repository
- Contact: vinoth.premkumar@tigeranalytics.com

---

## License

Internal PepsiCo project. All rights reserved.