# STTM-to-Notebook Generator

system that converts Source-to-Target Mapping (STTM) Excel files into complete Databricks ETL notebooks using Azure OpenAI.

## Quick Start

### Prerequisites
- Python 3.8+
- Git
- Azure OpenAI API access

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

## 📋 API Usage

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

## 🏗️ Architecture

### Components:
1. **API1 (JSON Converter)**: Converts STTM Excel → Structured JSON
2. **API2 (Notebook Generator)**: Generates Databricks ETL notebooks
3. **API3 (Orchestrator)**: Coordinates the entire process

### Key Features:
- ✅ Azure OpenAI Integration
- ✅ Semantic Validation
- ✅ Error Handling & Logging
- ✅ Template-based Code Generation
- ✅ Audit Framework Integration
- ✅ Data Quality Rules Support

## 📁 Project Structure

```
POD3/
├── sttm_to_notebook_generator_integrated/
│   ├── api1_json_converter.py      # STTM to JSON conversion
│   ├── api3_sttm_to_notebook_generator.py  # Main orchestrator
│   └── log_handler.py              # Logging utilities
├── notebook_generator_app/
│   ├── main.py                     # API2 - Notebook generation
│   ├── llm/langchain_workflow.py   # LLM integration
│   └── utilities/helpers.py        # Helper functions
├── templates/
│   ├── silver/                     # Silver layer templates
│   └── gold/                       # Gold layer templates
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🔧 Configuration

### Azure OpenAI Setup
The system is configured to use Azure OpenAI with the following settings:
- **Model**: gpt-4o
- **API Version**: 2024-07-01-preview
- **Temperature**: 0.0 (for consistent outputs)

### Template System
- Templates are located in `templates/` directory
- Supports both Silver and Gold layer transformations
- Project-specific templates can be added for customization

## 🐛 Troubleshooting

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
   - Verify Azure OpenAI credentials in `.env`
   - Check API quota and limits

## 📝 Version History

### v1.0.0 (Current)
- ✅ Complete STTM-to-Notebook pipeline
- ✅ Azure OpenAI integration
- ✅ Semantic validation
- ✅ Error handling
- ✅ Template system

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Your License Here]

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Contact: [your-email@domain.com]
