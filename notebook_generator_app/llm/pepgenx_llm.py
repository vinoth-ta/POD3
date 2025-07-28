from dotenv import load_dotenv
from typing import List, Any
import os
import requests
import time
import logging
from litellm import ModelResponse
from sttm_to_notebook_generator_integrated.log_handler import get_logger


load_dotenv()
# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
logger = get_logger("<API2 :: CodeGenerator>")

class PepGenXLLMWrapper:
    """
    PepGenXLLMWrapper handles interactions with an internal LLM API, including authentication
    and prompt completion.  It manages bearer token retrieval using client credentials
    and makes POST requests to a specified model URL.

    This class is designed to work indepedently of LiteLLM.  It should be used directly or
    through a wrapper class like LangChainWrapper for LangChain compatibility.

    Attributes:
        token_url (str): OAuth2 token URL for bearer token retrieval
        model_url (str): Endpoint for the LLM completion API
        model_name (str): Name of the model to use
        client_id (str): OAuth2 Client ID
        client_secret (str): OAuth2 Client Secret
    """
    def __init__(self, token_url: str, model_url: str, model_name: str, client_id: str, client_secret: str):
        self.token_url = token_url
        self.model_url = model_url
        self.model_name = model_name
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_expiry = 0
        self._token_lifetime = 3600
        self._create_bearer_token()

    def _create_bearer_token(self):
        """
        Retrieves a bearer token from the token URL using client credentials.

        Returns:
            str: Bearer access token
        """
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(self.token_url, data=payload, headers=headers)
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            self._token = access_token
            self._token_expiry = time.time() + self._token_lifetime
        else:
            logger.info(f"[ERROR]: {response.status_code}: {response.text}")
            response.raise_for_status()

    def _ensure_valid_token(self):
        """
        Ensures that the current bearer token is valid.
        Refreshes the token if it is missing or expired.
        """
        if self._token is None or time.time() > self._token_expiry - 60:
            self._create_bearer_token()

    def completion(self, model: str, messages: List[dict], **kwargs: Any) -> ModelResponse:
        """
        Sends a prompt to the internal model API and retrieves the generated completion.

        Args:
            model (str): Name of the model
            messages (List[dict]): A list of message dicts with role and content
            **kwargs: Additional keyword arguments

        Returns:
            ModelResponse: A result object containing the generated content in the 'choices' field
        """
        self._ensure_valid_token()
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "team_id": "c0b5155f-009a-4410-a2c9-af0644beb169",
            "project_id": "5747984e-464d-435b-b542-dc7a12cde42e",
            "x-pepgenx-apikey": os.getenv("PEPGENX_API_KEY"),
        }
        # generate-response payload
        prompt = messages[-1]["content"]
        payload = {
            # "generation_model": "claude-3-5-sonnet",
            "prompt": prompt
        }
        # generate-reasoning-response payload
        # prompt = self.build_prompt(messages) # Required for Reasoning Model
        # payload = {
        #     "custom_prompt": prompt,
        #     "temperature": 0
        # }
        response = requests.post(
            url=self.model_url,
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            return ModelResponse(choices=[{"message": {"content": result['response']}}])
        else:
            logger.error(f"[ERROR]: {response.status_code}: {response.text}")
            response.raise_for_status()

    def build_prompt(self, messages: List[dict]) -> str:
        """
        This method is only used when calling the Reasoning Model
        
        Constructs a formatted prompt string from a list of messages.
        Each method is expected to contain a 'role' and 'content' key.
        Roles must be 'system', 'user', or 'assistant'

        Args:
            messages (List[dict]): A list of message dicts to format

        Returns:
            str: A single formatted string representing the complete prompt
        """
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"[System]: {content}\n"
            elif role == "user":
                prompt += f"[User]: {content}\n"
            elif role == "assistant":
                prompt += f"[Assistant]: {content}\n"
        return prompt.strip()