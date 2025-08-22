from __future__ import annotations

import os
from abc import ABC, abstractmethod
from logging import Logger, getLogger
from typing import AsyncGenerator, Generator

logger: Logger = getLogger(__name__)


class AsyncLLMProvider(ABC):
    def __init__(self, model: str = None):
        self.model = model

    @abstractmethod
    async def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """
        Get the response from an LLM model.
        """
        pass

    @abstractmethod
    async def get_tools_response(
        self,
        chat_history: list[dict[str, str]],
        tools: list[dict[str, str]],
        temperature: float = 0,
        **kwargs,
    ) -> dict[str, list[dict] | str]:
        """
        Get the response from an LLM model from OpenAI with tools.
        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            tools (list[dict[str, str]]): List of tools to use in the completion.
                See https://platform.openai.com/docs/guides/function-calling#advanced-usage.
            temperature (float): Temperature for the model. Default to 0.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        Returns:
            dict[str, list[dict] | str]: The response from the LLM model. Keys:
                - func_names (list[str]): List of function names.
                - arguments (list[dict]): List of arguments for each function
                - text (str): The text content of the message, if any.
        """
        pass

    @abstractmethod
    async def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Get a streaming response from an LLM model.
        """
        pass


class AsyncLLMEngine:
    def __init__(self, model: str = None):
        if model is None:
            model = os.getenv("BIGDATA_RESEARCH_DEFAULT_LLM")
            source = "Environment"
        else:
            source = "Argument"

        try:
            self.provider, self.model = model.split("::")
        except (ValueError, AttributeError):
            logger.error(
                f"Invalid model format. It should be `<provider>::<model>`."
                f"\nModel: {model}. Source: {source}",
            )

            raise ValueError(
                "Invalid model format. It should be `<provider>::<model>`."
            )

        self.provider = self.load_provider()

    def load_provider(self) -> AsyncLLMProvider:
        provider = self.provider.lower()
        if provider == "openai":
            from bigdata_research_tools.llm.openai import AsyncOpenAIProvider

            return AsyncOpenAIProvider(model=self.model)

        elif provider == "bedrock":
            from bigdata_research_tools.llm.bedrock import AsyncBedrockProvider
            
            return AsyncBedrockProvider(model=self.model)
        else:
            logger.error(f"Invalid provider: `{self.provider}`")

            raise ValueError("Invalid provider")

    async def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        return await self.provider.get_response(chat_history, **kwargs)

    async def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        return await self.provider.get_stream_response(chat_history, **kwargs)

    async def get_tools_response(
        self,
        chat_history: list[dict[str, str]],
        tools: list[dict[str, str]],
        temperature: float = 0,
        **kwargs,
    ) -> dict[str, list[dict] | str]:
        """
        Get the response from an LLM model from OpenAI with tools.
        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            tools (list[dict[str, str]]): List of tools to use in the completion.
                See https://platform.openai.com/docs/guides/function-calling#advanced-usage.
            temperature (float): Temperature for the model. Default to 0.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        Returns:
            dict[str, list[dict] | str]: The response from the LLM model. Keys:
                - func_names (list[str]): List of function names.
                - arguments (list[dict]): List of arguments for each function
                - text (str): The text content of the message, if any.
        """
        return await self.provider.get_tools_response(
            chat_history, tools, temperature, **kwargs
        )


class LLMProvider(ABC):
    def __init__(self, model: str = None):
        self.model = model

    @abstractmethod
    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """
        Get the response from an LLM model.
        """
        pass

    @abstractmethod
    def get_tools_response(
        self,
        chat_history: list[dict[str, str]],
        tools: list[dict[str, str]],
        temperature: float = 0,
        **kwargs,
    ) -> dict[str, list[dict] | str]:
        """
        Get the response from an LLM model from OpenAI with tools.
        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            tools (list[dict[str, str]]): List of tools to use in the completion.
                See https://platform.openai.com/docs/guides/function-calling#advanced-usage.
            temperature (float): Temperature for the model. Default to 0.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        Returns:
            dict[str, list[dict] | str]: The response from the LLM model. Keys:
                - func_names (list[str]): List of function names.
                - arguments (list[dict]): List of arguments for each function
                - text (str): The text content of the message, if any.
        """
        pass

    @abstractmethod
    def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """
        Get a streaming response from an LLM model.
        """
        pass


class LLMEngine:
    def __init__(self, model: str = None):
        if model is None:
            model = os.getenv("BIGDATA_RESEARCH_DEFAULT_LLM")
            source = "Environment"
        else:
            source = "Argument"

        try:
            self.provider, self.model = model.split("::")
        except (ValueError, AttributeError):
            logger.error(
                f"Invalid model format. It should be `<provider>::<model>`."
                f"\nModel: {model}. Source: {source}",
            )

            raise ValueError(
                "Invalid model format. It should be `<provider>::<model>`."
            )

        self.provider = self.load_provider()

    def load_provider(self) -> LLMProvider:
        provider = self.provider.lower()
        if provider == "openai":
            from bigdata_research_tools.llm.openai import OpenAIProvider

            return OpenAIProvider(model=self.model)
        elif provider == "bedrock":
            from bigdata_research_tools.llm.bedrock import BedrockProvider

            return BedrockProvider(model=self.model)
        else:
            logger.error(f"Invalid provider: `{self.provider}`")

            raise ValueError("Invalid provider")

    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        return self.provider.get_response(chat_history, **kwargs)

    def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        return self.provider.get_stream_response(chat_history, **kwargs)

    def get_tools_response(
        self,
        chat_history: list[dict[str, str]],
        tools: list[dict[str, str]],
        temperature: float = 0,
        **kwargs,
    ) -> dict[str, list[dict] | str]:
        """
        Get the response from an LLM model from OpenAI with tools.
        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            tools (list[dict[str, str]]): List of tools to use in the completion.
                See https://platform.openai.com/docs/guides/function-calling#advanced-usage.
            temperature (float): Temperature for the model. Default to 0.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        Returns:
            dict[str, list[dict] | str]: The response from the LLM model. Keys:
                - func_names (list[str]): List of function names.
                - arguments (list[dict]): List of arguments for each function
                - text (str): The text content of the message, if any.
        """
        return self.provider.get_tools_response(
            chat_history, tools, temperature, **kwargs
        )
