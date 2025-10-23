# my_fastapi_app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("endpoint") or os.getenv("AZURE_OPENAI_ENDPOINT", "https://testacceleratoropenai.openai.azure.com/")
AZURE_OPENAI_DEPLOYMENT = os.getenv("deployment") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-testaccelerator")
AZURE_OPENAI_API_VERSION = os.getenv("api_version") or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_API_KEY = os.getenv("subscription_key") or os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_MODEL_NAME = os.getenv("model_name", "gpt-4")

# Databricks Configuration
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# PepGenX Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_URL = os.getenv("TOKEN_URL")
TEAM_ID = os.getenv("TEAM_ID")
PROJECT_ID = os.getenv("PROJECT_ID")
PEPGENX_API_KEY = os.getenv("PEPGENX_API_KEY")
MODEL_URL = os.getenv("MODEL_URL")

# Application Configuration
rootContext = os.getenv("ROOTCONTEXT", "silver-codegen-genai")
