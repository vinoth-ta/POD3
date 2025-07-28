# my_fastapi_app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env only once when config.py is first imported
load_dotenv(dotenv_path=Path(__file__).parent / "json_generator.env")

# Access environment variables
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_URL = os.getenv("TOKEN_URL")
TEAM_ID = os.getenv("TEAM_ID")
PROJECT_ID = os.getenv("PROJECT_ID")
PEPGENX_API_KEY = os.getenv("PEPGENX_API_KEY")
MODEL_URL = os.getenv("MODEL_URL")
rootContext=MODEL_URL = os.getenv("ROOTCONTEXT")
