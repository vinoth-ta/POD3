from typing import List, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class LangChainWrapper(BaseChatModel):
    """
    A LangChain-compatible wrapper for the PepGenX Custom Model.
    Implements the BaseChatModel interface, allowing it to be used with the LangChain's prompt templates and chains.

    Attributes:
        custom_model (PepGenXLLMWrapper): An instance of the internal model handler
    """
    def __init__(self, custom_model, **kwargs):
        super().__init__(**kwargs)
        self._custom_model = custom_model

    def _call(self, messages: List[BaseMessage], **kwargs) -> str:
        """
        LangChain interface private method that builds a prompt from a list of messages
        and sends it to the custom model for completion.

        Args:
            messages (List[BaseMessage]): List of LangChain message objects
            **kwargs: Additional arguments

        Returns:
            str: The generated text content from the model
        """
        prompt = ""
        for message in messages:
            if isinstance(message, SystemMessage):
                prompt += f"System: {message.content}\n"
            elif isinstance(message, HumanMessage):
                prompt += f"{message.content}\n"

        response = self._custom_model.completion(
            model=self._custom_model.model_name,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0]["message"]["content"]
    
    def _generate(self, messages: List[BaseMessage], stop: List[str] = None, **kwargs: Any) -> "ChatResult":
        """
        Implements the `_generate` private method expected by LangChain for custom models, wrapping the internal
        `_call` to return a structured ChatResult object.

        Args:
            messages (List[BaseMessage]): List of input messages (system + user)
            stop (Optional[List[str]]): Stop sequences for generation
            **kwargs (Any): Additional arguments passed to `_call`

        Returns:
            ChatResult: A result containing the generated AI message
        """
        response_text = self._call(messages, **kwargs)
        message = AIMessage(content=response_text)

        return ChatResult(
            generations=[ChatGeneration(message=message)]
        )
    
    @property
    def _llm_type(self) -> str:
        """
        Returns a string identifier for this custom LLM type.

        Returns:
            str: Type identifier for LangChain to recognize
        """
        return "custom_internal_model"