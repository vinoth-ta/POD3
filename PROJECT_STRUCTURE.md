# STTM-to-Notebook Generator: Project Structure

## Overview
This document outlines the organized structure of the STTM-to-Notebook Generator project, providing a clear understanding of where different components are located and their purposes.

## Root Directory Structure

```
POD3/
├── README.md                           # Main project documentation
├── requirements.txt                    # Python dependencies
├── .gitignore                         # Git ignore rules
├── .dockerignore                      # Docker ignore rules
├── Dockerfile                         # Docker container configuration
├── docker-compose.yml                 # Docker Compose configuration
├── PROJECT_STRUCTURE.md               # This file - project structure guide
│
├── docs/                              # Documentation directory
│   ├── architecture/                  # System architecture diagrams
│   │   ├── v1.0.0_architecture_diagrams.md
│   │   └── v1.1.0_architecture_diagrams.md
│   ├── analysis/                      # Technical analysis documents
│   │   ├── comprehensive_technical_analysis.md
│   │   ├── version_comparison_analysis.md
│   │   └── token_analysis_report.md
│   └── deployment/                    # Deployment documentation
│       └── DEPLOYMENT.md
│
├── sttm_to_notebook_generator_integrated/  # Main application code
│   ├── __init__.py
│   ├── api1_json_converter.py             # Original STTM to JSON converter
│   ├── api1_json_converter_optimized.py   # Optimized STTM to JSON converter
│   ├── api3_sttm_to_notebook_generator.py # Main orchestrator
│   ├── log_handler.py                     # Logging utilities
│   ├── log_session_id.py                  # Session management
│   └── read_env_var.py                    # Environment variable handling
│
├── notebook_generator_app/            # Notebook generation application
│   ├── __init__.py
│   ├── main.py                         # FastAPI application for notebook generation
│   ├── llm/                            # LLM integration layer
│   │   ├── __init__.py
│   │   ├── langchain_workflow.py       # LangChain workflow integration
│   │   ├── langchain_wrapper.py        # LangChain wrapper utilities
│   │   └── pepgenx_llm.py              # PepGenX LLM integration
│   ├── schemas/                        # Data schemas and models
│   │   ├── __init__.py
│   │   └── models.py                   # Pydantic models
│   └── utilities/                      # Utility functions
│       ├── __init__.py
│       └── helpers.py                  # Helper functions
│
├── templates/                          # Jinja2 templates for notebook generation
│   ├── gold/                           # Gold layer templates
│   │   ├── gold_notebook_template.j2
│   │   ├── instructions_langchain.txt
│   │   ├── system_prompt_sttm.txt
│   │   ├── system_prompt_validator.txt
│   │   └── system_prompt.txt
│   └── silver/                         # Silver layer templates
│       ├── instructions_langchain.txt
│       ├── silver_notebook_template.j2
│       ├── system_prompt_dedupe_staledata.txt
│       ├── system_prompt_dedupe.txt
│       ├── system_prompt_multisilver_dedupe_staledata.txt
│       ├── system_prompt_multisilver_dedupe.txt
│       ├── system_prompt_multisilver.txt
│       ├── system_prompt.txt
│       └── corporate_social_responsibility/
│           └── emissions_tracking/
│               ├── instructions_langchain.txt
│               ├── silver_notebook_template.j2
│               └── system_prompt.txt
│
├── static/                             # Static web assets
│   ├── css/
│   │   └── styles.css
│   ├── img/
│   │   └── PepsiCo_logo.png
│   ├── js/
│   │   ├── script.js
│   │   └── script_og.js
│   └── index.html
│
├── tests/                              # Testing directory
│   ├── automated/                      # Automated test scripts
│   │   └── test_comparison.py          # Automated version comparison tests
│   ├── manual/                         # Manual test scripts
│   │   └── manual_test_comparison.py   # Manual version comparison tests
│   └── results/                        # Test results and outputs
│       ├── test_results_v1.0.0_20250728_205813.json
│       └── test_results_v1.1.0_20250728_205835.json
│
├── data/                               # Data directory
│   ├── sample_sttm/                    # Sample STTM files for testing
│   │   ├── Corporate_Social_Responsibility_XTNElectricityBasedEmission.xlsx
│   │   ├── Corporate_Social_Responsibility_XTNElectricityBasedEmission_multi_source_same_column.xlsx
│   │   ├── Corporate_Social_Responsibility_XTNElectricityBasedEmission_multi_source_same_column_modified.xlsx
│   │   └── Corporate_Social_Responsibility_XTNFuelBasedEmission.xlsx
│   └── responses/                      # API response data
│       ├── v1.0.0_response.json
│       └── v1.1.0_response.json
│
├── scripts/                            # Utility scripts
│   ├── analysis/                       # Analysis scripts
│   │   └── token_analysis.py           # Token usage analysis script
│   └── setup/                          # Setup and deployment scripts
│       └── setup.sh                    # Local environment setup script
│
├── devops/                             # DevOps and CI/CD configuration
│   └── config/                         # Configuration files
│       ├── cicd_pipeline.yaml          # CI/CD pipeline configuration
│       ├── common/                     # Common configuration
│       │   └── variables.yaml
│       ├── dev/                        # Development environment config
│       │   ├── values.yaml
│       │   └── variables.yaml
│       ├── preprod/                    # Pre-production environment config
│       │   ├── values.yaml
│       │   └── variables.yaml
│       ├── prod/                       # Production environment config
│       │   ├── values.yaml
│       │   └── variables.yaml
│       └── qa/                         # QA environment config
│           ├── values.yaml
│           └── variables.yaml
│
├── logs/                               # Application logs directory
├── venv/                               # Python virtual environment (gitignored)
└── .DS_Store                           # macOS system file (gitignored)
```

## Directory Purposes

### `/docs/`
Contains all project documentation organized by category:
- **architecture/**: Mermaid diagrams and system architecture documentation
- **analysis/**: Technical analysis, comparison reports, and performance metrics
- **deployment/**: Deployment guides and configuration documentation

### `/sttm_to_notebook_generator_integrated/`
Core application code containing:
- **API1**: STTM to JSON conversion (original and optimized versions)
- **API3**: Main orchestrator that coordinates the entire process
- **Utilities**: Logging, session management, and environment handling

### `/notebook_generator_app/`
Notebook generation application with:
- **LLM Integration**: LangChain workflows and LLM wrappers
- **Schemas**: Data models and validation
- **Utilities**: Helper functions and common utilities

### `/templates/`
Jinja2 templates for generating Databricks notebooks:
- **Gold Layer**: Templates for gold layer transformations
- **Silver Layer**: Templates for silver layer transformations
- **Project-specific**: Custom templates for specific domains

### `/tests/`
Testing infrastructure:
- **Automated**: Scripts for automated testing and comparison
- **Manual**: Manual testing procedures and scripts
- **Results**: Test outputs and comparison data

### `/data/`
Data files and samples:
- **Sample STTM**: Example STTM files for testing and development
- **Responses**: API response data for analysis and comparison

### `/scripts/`
Utility scripts for various tasks:
- **Analysis**: Data analysis and performance measurement scripts
- **Setup**: Environment setup and deployment scripts

### `/devops/`
DevOps and deployment configuration:
- **CI/CD**: Pipeline configurations
- **Environment Configs**: Different environment-specific configurations

## Key Files

### Root Level
- **README.md**: Main project documentation and quick start guide
- **requirements.txt**: Python package dependencies
- **Dockerfile**: Container configuration for deployment
- **docker-compose.yml**: Multi-container deployment setup

### Configuration
- **.gitignore**: Specifies files to exclude from version control
- **.dockerignore**: Specifies files to exclude from Docker builds

## Benefits of This Structure

1. **Clear Separation**: Each directory has a specific purpose and responsibility
2. **Easy Navigation**: Developers can quickly find relevant files
3. **Scalable**: Structure supports future growth and new features
4. **Maintainable**: Organized code is easier to maintain and update
5. **Documentation**: Comprehensive documentation is easily accessible
6. **Testing**: Dedicated testing structure supports quality assurance
7. **Deployment**: Clear separation of deployment and configuration files

## Version Control

The project uses Git for version control with:
- **Main branch**: Contains the latest stable code
- **Version tags**: v1.0.0 and v1.1.0 for specific releases
- **Organized commits**: Clear commit messages and logical grouping

---

*Project structure documentation for STTM-to-Notebook Generator*
*Last updated: July 29, 2025* 