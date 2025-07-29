# STTM-to-Notebook Generator: Project Structure

## Overview
This project implements an AI-powered system that converts Source-to-Target Mapping (STTM) Excel files into executable Databricks notebooks. The system uses advanced LLM integration and multi-agent orchestration to generate high-quality ETL code.

## Directory Structure

```
POD3/
├── sttm_to_notebook_generator_integrated/    # Main API integration module
│   ├── __init__.py
│   ├── api1_json_converter.py               # V1.0.0: Original JSON converter
│   ├── api1_json_converter_optimized.py     # V1.1.0: Optimized JSON converter
│   ├── api3_sttm_to_notebook_generator.py   # V1.1.0: Main FastAPI app
│   ├── log_handler.py                       # Logging utilities
│   ├── log_session_id.py                    # Session management
│   └── read_env_var.py                      # Environment configuration
│
├── notebook_generator_app/                   # Notebook generation module
│   ├── __init__.py
│   ├── main.py                              # Notebook generation API
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py                        # Pydantic models
│   ├── utilities/
│   │   ├── __init__.py
│   │   └── helpers.py                       # Utility functions
│   └── llm/
│       ├── __init__.py
│       ├── langchain_workflow.py            # LangChain integration
│       ├── langchain_wrapper.py             # LLM wrapper
│       └── pepgenx_llm.py                   # PepGenX LLM integration
│
├── templates/                                # Jinja2 templates
│   ├── gold/
│   │   ├── gold_notebook_template.j2
│   │   ├── instructions_langchain.txt
│   │   ├── system_prompt_sttm.txt
│   │   ├── system_prompt_validator.txt
│   │   └── system_prompt.txt
│   └── silver/
│       ├── corporate_social_responsibility/
│       │   └── emissions_tracking/
│       │       ├── instructions_langchain.txt
│       │       ├── silver_notebook_template.j2
│       │       └── system_prompt.txt
│       ├── instructions_langchain.txt
│       ├── silver_notebook_template.j2
│       ├── system_prompt_dedupe_staledata.txt
│       ├── system_prompt_dedupe.txt
│       ├── system_prompt_multisilver_dedupe_staledata.txt
│       ├── system_prompt_multisilver_dedupe.txt
│       ├── system_prompt_multisilver.txt
│       └── system_prompt.txt
│
├── static/                                   # Static web assets
│   ├── css/
│   │   └── styles.css
│   ├── img/
│   │   └── PepsiCo_logo.png
│   ├── js/
│   │   ├── script.js
│   │   └── script_og.js
│   └── index.html
│
├── tests/                                    # Testing directory
│   ├── automated/                            # Automated test scripts
│   │   └── test_comparison.py                # Automated version comparison tests
│   ├── manual/                               # Manual test scripts
│   │   └── manual_test_comparison.py         # Manual version comparison tests
│   └── results/                              # Test results and outputs
│       ├── version_comparison_report_*.md    # Generated comparison reports
│       ├── version_stats_*.json              # Detailed statistics
│       ├── test_results_v1.0.0_*.json       # V1.0.0 test results
│       └── test_results_v1.1.0_*.json       # V1.1.0 test results
│
├── data/                                     # Data directory
│   ├── sample_sttm/                          # Sample STTM files for testing
│   │   ├── Corporate_Social_Responsibility_XTNElectricityBasedEmission.xlsx
│   │   ├── Corporate_Social_Responsibility_XTNElectricityBasedEmission_multi_source_same_column.xlsx
│   │   ├── Corporate_Social_Responsibility_XTNElectricityBasedEmission_multi_source_same_column_modified.xlsx
│   │   └── Corporate_Social_Responsibility_XTNFuelBasedEmission.xlsx
│   └── responses/                            # API response data
│       ├── v1.0.0_response.json             # V1.0.0 response samples
│       └── v1.1.0_response.json             # V1.1.0 response samples
│
├── scripts/                                  # Utility scripts
│   ├── analysis/                             # Analysis scripts
│   │   ├── token_analysis.py                 # Token usage analysis script
│   │   ├── extract_version_stats.py          # Version statistics extractor
│   │   └── view_existing_stats.py            # Existing stats viewer
│   ├── setup/                                # Setup and deployment scripts
│   │   └── setup.sh                          # Local environment setup script
│   └── run_parallel.py                       # Parallel server runner
│
├── docs/                                     # Documentation
│   ├── analysis/                             # Analysis documentation
│   │   ├── comprehensive_technical_analysis.md
│   │   ├── token_analysis_report.md
│   │   └── version_comparison_analysis.md
│   ├── architecture/                         # Architecture documentation
│   │   ├── v1.0.0_architecture_diagrams.md
│   │   └── v1.1.0_architecture_diagrams.md
│   └── deployment/                           # Deployment documentation
│       └── DEPLOYMENT.md
│
├── devops/                                   # DevOps and CI/CD configuration
│   └── config/
│       ├── cicd_pipeline.yaml
│       ├── common/
│       │   └── variables.yaml
│       ├── dev/
│       │   ├── values.yaml
│       │   └── variables.yaml
│       ├── preprod/
│       │   ├── values.yaml
│       │   └── variables.yaml
│       ├── prod/
│       │   ├── values.yaml
│       │   └── variables.yaml
│       ├── qa/
│       │   ├── values.yaml
│       │   └── variables.yaml
│       └── variables.yaml
│
├── logs/                                     # Application logs
│   └── .gitkeep                              # Keep directory in git
│
├── venv/                                     # Python virtual environment
├── .git/                                     # Git repository
├── .gitignore                                # Git ignore rules
├── .dockerignore                             # Docker ignore rules
├── README.md                                 # Project overview
├── PROJECT_STRUCTURE.md                      # This file
├── requirements.txt                          # Python dependencies
├── Dockerfile                                # Docker configuration
└── docker-compose.yml                        # Docker Compose configuration
```

## Key Components

### API Modules
- **V1.0.0**: `api1_json_converter.py` - Original implementation
- **V1.1.0**: `api1_json_converter_optimized.py` - Optimized implementation
- **Main App**: `api3_sttm_to_notebook_generator.py` - FastAPI orchestrator

### Testing Framework
- **Automated Tests**: `tests/automated/test_comparison.py`
- **Manual Tests**: `tests/manual/manual_test_comparison.py`
- **Statistics**: `scripts/analysis/extract_version_stats.py`
- **Parallel Testing**: `scripts/run_parallel.py`

### Analysis Tools
- **Token Analysis**: `scripts/analysis/token_analysis.py`
- **Version Stats**: `scripts/analysis/extract_version_stats.py`
- **Stats Viewer**: `scripts/analysis/view_existing_stats.py`

## Version Management

### V1.0.0 (Original)
- Uses `api1_json_converter.py`
- Basic validation and error handling
- Standard processing pipeline

### V1.1.0 (Optimized)
- Uses `api1_json_converter_optimized.py`
- Enhanced validation and smart error recovery
- Improved performance and quality
- Better LLM integration

## Usage

### Running Individual Versions
```bash
# V1.1.0 (Current)
uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8000 --reload

# V1.0.0 (Using parallel runner)
python scripts/run_parallel.py
```

### Running Tests
```bash
# Extract fresh statistics
python scripts/analysis/extract_version_stats.py

# View existing statistics
python scripts/analysis/view_existing_stats.py

# Run automated comparison
python tests/automated/test_comparison.py
```

### Analysis
```bash
# Token usage analysis
python scripts/analysis/token_analysis.py

# Generate comparison reports
python scripts/analysis/extract_version_stats.py
```

## File Organization

### Scripts Organization
- **Analysis Scripts**: `scripts/analysis/` - Statistics and analysis tools
- **Setup Scripts**: `scripts/setup/` - Environment setup and deployment
- **Utility Scripts**: `scripts/` - General utilities like parallel runner

### Test Organization
- **Automated Tests**: `tests/automated/` - Automated test suites
- **Manual Tests**: `tests/manual/` - Manual testing procedures
- **Test Results**: `tests/results/` - Generated test outputs

### Data Organization
- **Sample Data**: `data/sample_sttm/` - Test STTM files
- **Response Data**: `data/responses/` - API response samples
- **Logs**: `logs/` - Application logs (cleaned)

## Cleanup and Maintenance

### Regular Cleanup
- Python cache files (`__pycache__/`, `*.pyc`) are automatically ignored
- Log files are cleaned regularly
- Test results are preserved for analysis
- Temporary files are excluded from version control

### Git Organization
- Clean project structure with proper .gitignore
- Organized commit history
- Clear separation of concerns
- Proper documentation maintenance

---
*Last updated: July 29, 2025* 