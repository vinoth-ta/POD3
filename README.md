# STTM-to-Notebook Generator v1.1.0

Advanced system that converts Source-to-Target Mapping (STTM) Excel files into complete Databricks ETL notebooks using Gen AI (LLM) with enhanced performance and optimized processing.

## Quick Start

### Prerequisites
- Python 3.8+
- Git
- LLM API access

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd POD3
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-07-01-preview
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### 5. Start the Application
```bash
uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

## API Usage

### Endpoint: `/from-sttm-generate-notebook`

**Method:** POST  
**Content-Type:** multipart/form-data

**Request Body:**
- `file`: STTM Excel file
- `sttm_metadata_json`: JSON string with file metadata
- `notebook_metadata_json`: JSON string with notebook configuration

**Example Request:**
```bash
curl -X POST "http://localhost:8000/from-sttm-generate-notebook" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_sttm_file.xlsx" \
  -F "sttm_metadata_json=[{\"file_name\":\"your_file.xlsx\",\"sheet_name\":\"Sheet1\",\"table_name\":\"YourTable\",\"target_table_name\":\"YourTargetTable\"}]" \
  -F "notebook_metadata_json={\"user_id\":\"your_user_id\",\"table_load_type\":\"silver\",\"domain\":\"your_domain\",\"product\":\"your_product\"}"
```

**Response:**
```json
{
  "success": true,
  "message": "Notebook generated successfully.",
  "notebook_id": "TODO",
  "notebook_name": "generated_notebook.py",
  "data": "# Generated Databricks notebook content..."
}
```

## Architecture

### Components:
1. **API1 (JSON Converter)**: Converts STTM Excel → Structured JSON
   - **Optimized Version**: `api1_json_converter_optimized.py` - Enhanced performance with smart validation
   - **Original Version**: `api1_json_converter.py` - Backup version
2. **API2 (Notebook Generator)**: Generates Databricks ETL notebooks
3. **API3 (Orchestrator)**: Coordinates the entire process using optimized components

### Key Features:
- Azure OpenAI Integration
- Enhanced Performance with Optimized Processing
- Smart Validation & Error Recovery
- Semantic Validation
- Error Handling & Logging
- Template-based Code Generation
- Audit Framework Integration
- Data Quality Rules Support
- Multi-attempt JSON Generation with Feedback Loop

## Project Structure

The project follows a well-organized structure for maintainability and scalability:

```
POD3/
├── README.md                           # Main project documentation
├── PROJECT_STRUCTURE.md               # Detailed project structure guide
├── requirements.txt                    # Python dependencies
├── .gitignore                         # Git ignore rules
├── Dockerfile                         # Docker container configuration
├── docker-compose.yml                 # Docker Compose configuration
│
├── docs/                              # Documentation directory
│   ├── architecture/                  # System architecture diagrams
│   ├── analysis/                      # Technical analysis documents
│   └── deployment/                    # Deployment documentation
│
├── sttm_to_notebook_generator_integrated/  # Main application code
│   ├── api1_json_converter_optimized.py   # Optimized STTM to JSON conversion
│   ├── api1_json_converter.py             # Original STTM to JSON conversion (backup)
│   ├── api3_sttm_to_notebook_generator.py # Main orchestrator
│   └── log_handler.py                     # Logging utilities
│
├── notebook_generator_app/            # Notebook generation application
│   ├── main.py                         # FastAPI application for notebook generation
│   ├── llm/                            # LLM integration layer
│   ├── schemas/                        # Data schemas and models
│   └── utilities/                      # Utility functions
│
├── templates/                          # Jinja2 templates for notebook generation
│   ├── silver/                         # Silver layer templates
│   └── gold/                           # Gold layer templates
│
├── tests/                              # Testing directory
│   ├── automated/                      # Automated test scripts
│   ├── manual/                         # Manual test scripts
│   └── results/                        # Test results and outputs
│
├── data/                               # Data directory
│   ├── sample_sttm/                    # Sample STTM files for testing
│   └── responses/                      # API response data
│
├── scripts/                            # Utility scripts
│   ├── analysis/                       # Analysis scripts
│   └── setup/                          # Setup and deployment scripts
│
├── devops/                             # DevOps and CI/CD configuration
│   └── config/                         # Configuration files
│
├── static/                             # Static web assets
├── logs/                               # Application logs directory
└── venv/                               # Python virtual environment (gitignored)
```

For detailed information about the project structure, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## Configuration

### Azure OpenAI Setup
The system is configured to use Azure OpenAI with the following settings:
- **Model**: gpt-4o
- **API Version**: 2024-07-01-preview
- **Temperature**: 0.0 (for consistent outputs)

### Template System
- Templates are located in `templates/` directory
- Supports both Silver and Gold layer transformations
- Project-specific templates can be added for customization

## Troubleshooting

### Common Issues:

1. **Port Already in Use**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Module Not Found Errors**
   ```bash
   pip install -r requirements.txt
   ```

3. **Template Not Found**
   - Ensure templates directory exists in project root
   - Check file permissions

4. **LLM API Errors**
   - Verify LLM API credentials in `.env`
   - Check API quota and limits

## Version History

### v1.1.0 (Current)
- Optimized STTM processor with enhanced performance
- Smart validation and error recovery mechanisms
- Multi-attempt JSON generation with feedback loop
- Improved Azure OpenAI integration
- Enhanced error handling and logging

### v1.0.0
- Complete STTM-to-Notebook pipeline
- Azure OpenAI integration
- Semantic validation
- Error handling
- Template system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request


## Support

For issues and questions:
- Create an issue in the repository
- Contact: vinoth.premkumar@tigeranalytics.com
