from __future__ import annotations

import os
import warnings
from abc import ABC, abstractmethod
from logging import Logger, getLogger
from typing import AsyncGenerator, Generator

from pydantic import BaseModel, model_validator

logger: Logger = getLogger(__name__)

REASONING_MODELS = ["gpt-5", "o1", "o2", "o3", "o4"]


class LLMConfig(BaseModel):
    """Configuration for LLM models."""

    model: str
    response_format: dict = {"type": "json_object"}
    temperature: float | None = None
    reasoning_effort: str | None = None
    top_p: float | None = 1
    frequency_penalty: int | None = 0
    presence_penalty: int | None = 0
    seed: int | None = 42
    max_completion_tokens: int | None = 300

    @model_validator(mode="after")
    def check_temperature_and_reasoning_effort(self):
        ## Only one of temperature or reasoning_effort should be set.
        if self.temperature is not None and self.reasoning_effort is not None:
            raise ValueError(
                "Only one of temperature or reasoning_effort should be set."
            )
        if self.temperature is None and self.reasoning_effort is None:
            warnings.warn(
                "For the best experience, one of temperature or reasoning_effort should be set. "
                "The LLM Config will not assign any value to either parameter and the calls will be "
                "performed with the default model settings.",
                UserWarning,
                stacklevel=2,
            )
        return self

    @model_validator(mode="after")
    def validate_reasoning_config(self):
        if any(rm in self.model for rm in REASONING_MODELS):
            self.top_p = None
            self.frequency_penalty = None
            self.presence_penalty = None
            self.reasoning_effort = (
                self.reasoning_effort if self.reasoning_effort is not None else "high"
            )
            if self.temperature is not None:
                warnings.warn(
                    "The selected model does not support temperature settings. "
                    "The LLM Config will set temperature to None and reasoning_effort to its current value (if specified, defaults to 'high')",
                )
                self.temperature = None
        else:
            self.temperature = self.temperature if self.temperature is not None else 0
            if self.reasoning_effort is not None:
                warnings.warn(
                    "The selected model does not support reasoning modes. "
                    "The LLM Config will set reasoning_effort to None and temperature to its current value (if specified, defaults to 0)",
                )
                self.reasoning_effort = None
            # issue here is that we were not even returning a warning if the config is wrong (i.e. asking for 4o mini with reasoning_effort). If we drop the wrong parameter, we should either setting the right one to its best value or warn that we will fallback to default model settings.
        return self

    def get_llm_kwargs(
        self, remove_max_tokens: bool = False, remove_json_formatting: bool = False
    ) -> dict:
        config_dict = self.model_dump()
        if remove_max_tokens:
            config_dict.pop("max_completion_tokens", None)
        if remove_json_formatting:
            config_dict.pop("response_format", None)
        # Remove None values and model key
        return {k: v for k, v in config_dict.items() if v is not None and k != "model"}


class AsyncLLMProvider(ABC):
    def __init__(self, model: str | None = None):
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
    def __init__(self, model: str | None = None):
        if model is None:
            model = os.getenv("BIGDATA_RESEARCH_DEFAULT_LLM", "openai::gpt-4o-mini")
            source = "Environment"
        else:
            source = "Argument"

        try:
            self.provider_name, self.model = model.split("::")
        except (ValueError, AttributeError):
            logger.error(
                f"Invalid model format. It should be `<provider>::<model>`."
                f"\nModel: {model}. Source: {source}",
            )

            raise ValueError(
                "Invalid model format. It should be `<provider>::<model>`."
            )

        self.provider = self.load_provider(provider_name=self.provider_name)

    def load_provider(self, provider_name: str) -> AsyncLLMProvider:
        provider = provider_name.lower()
        if provider == "openai":
            from bigdata_research_tools.llm.openai import AsyncOpenAIProvider

            return AsyncOpenAIProvider(model=self.model)

        elif provider == "bedrock":
            from bigdata_research_tools.llm.bedrock import AsyncBedrockProvider

            return AsyncBedrockProvider(model=self.model)
        elif provider == "azure":
            from bigdata_research_tools.llm.azure import AsyncAzureProvider

            return AsyncAzureProvider(model=self.model)
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
    def __init__(self, model: str | None = None):
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
    def __init__(self, model: str | None = None):
        if model is None:
            model = os.getenv("BIGDATA_RESEARCH_DEFAULT_LLM", "openai::gpt-4o-mini")
            source = "Environment"
        else:
            source = "Argument"

        try:
            self.provider_name, self.model = model.split("::")
        except (ValueError, AttributeError):
            logger.error(
                f"Invalid model format. It should be `<provider>::<model>`."
                f"\nModel: {model}. Source: {source}",
            )

            raise ValueError(
                "Invalid model format. It should be `<provider>::<model>`."
            )

        self.provider = self.load_provider(provider_name=self.provider_name)

    def load_provider(self, provider_name: str) -> LLMProvider:
        provider = provider_name.lower()
        if provider == "openai":
            from bigdata_research_tools.llm.openai import OpenAIProvider

            return OpenAIProvider(model=self.model)
        elif provider == "bedrock":
            from bigdata_research_tools.llm.bedrock import BedrockProvider

            return BedrockProvider(model=self.model)
        elif provider == "azure":
            from bigdata_research_tools.llm.azure import AzureProvider

            return AzureProvider(model=self.model)
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


class NotInitializedLLMProviderError(Exception):
    """Exception raised when an LLM provider is not initialized properly."""

    def __init__(self, provider: LLMProvider | AsyncLLMProvider):
        message = f"LLM Provider has been used, but it has not been properly initialized. Provider type: {type(provider).__name__}"
        super().__init__(message)
