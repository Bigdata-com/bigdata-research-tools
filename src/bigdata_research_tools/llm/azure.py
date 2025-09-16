from __future__ import annotations

import asyncio
import random
import time
from json import loads
from typing import AsyncGenerator, Generator

try:
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AsyncAzureOpenAI, AzureOpenAI, OpenAIError
except ImportError:
    raise ImportError(
        "Missing optional dependency for Azure LLM OpenAI provider, "
        "please install `bigdata_research_tools[azure]` to enable them."
    )

from bigdata_research_tools.llm.base import AsyncLLMProvider, LLMProvider


class AsyncAzureProvider(AsyncLLMProvider):
    def __init__(
        self,
        model: str,
    ):
        super().__init__(model)
        self._client = None
        self.configure_azure_client()

    def configure_azure_client(self) -> None:
        """
        Implement a singleton pattern for the Azure OpenAI client.
        Delays the creation of the client until it's needed to facilitate
        loading the environment.

        Returns:
            OpenAI: The OpenAI client.
        """
        if not self._client:
            try:
                self._client = AsyncAzureOpenAI()
            except OpenAIError:
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(),
                    "https://cognitiveservices.azure.com/.default",
                )

                self._client = AsyncAzureOpenAI(
                    azure_ad_token_provider=token_provider,
                )

    async def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """
        Get the response from an LLM model from OpenAI.

        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        """
        max_retries = 5
        delay = 1 + random.random()  # initial delay in seconds
        for attempt in range(max_retries):
            try:
                chat_completion = await self._client.chat.completions.create(
                    messages=chat_history, model=self.model, **kwargs
                )

                return chat_completion.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(delay)
                delay = 2 * delay + random.random()  # exponential backoff

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
        response = await self._client.chat.completions.create(
            messages=chat_history,
            model=self.model,
            tools=tools,
            temperature=temperature,
            **kwargs,
        )
        message = response.choices[0].message
        output = {
            "func_names": [],
            "arguments": [],
            "text": message.content,
        }
        if function_calls := message.tool_calls if message.tool_calls else None:
            output = {
                "func_names": [f.function.name for f in function_calls],
                "arguments": [loads(f.function.arguments) for f in function_calls],
            }
        return output

    async def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Get a streaming response from an LLM model from OpenAI.

        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        Returns:
            Generator[str, None, None]: A generator that yields the response from the LLM model.
        """
        async for delta in await self._client.chat.completions.create(
            model=self.model, messages=chat_history, stream=True, **kwargs
        ):
            if not delta.choices:
                continue
            last_content = delta.choices[0].delta.content or ""
            yield last_content


class AzureProvider(LLMProvider):
    def __init__(
        self,
        model: str,
    ):
        super().__init__(model)
        self._client = None
        self.configure_azure_client()

    def configure_azure_client(self) -> None:
        """
        Implement a singleton pattern for the Azure OpenAI client.
        Delays the creation of the client until it's needed to facilitate
        loading the environment.

        Returns:
            OpenAI: The OpenAI client.
        """
        if not self._client:
            try:
                self._client = AzureOpenAI()
            except OpenAIError:
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(),
                    "https://cognitiveservices.azure.com/.default",
                )

                self._client = AzureOpenAI(
                    azure_ad_token_provider=token_provider,
                )

    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """
        Get the response from an LLM model from Azure OpenAI.

        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        """

        max_retries = 5
        delay = 1 + random.random()  # initial delay in seconds
        for attempt in range(max_retries):
            try:
                chat_completion = self._client.chat.completions.create(
                    messages=chat_history, model=self.model, **kwargs
                )

                return chat_completion.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)
                delay = 2 * delay + random.random()  # exponential backoff

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
        response = self._client.chat.completions.create(
            messages=chat_history,
            model=self.model,
            tools=tools,
            temperature=temperature,
            **kwargs,
        )
        message = response.choices[0].message
        output = {
            "func_names": [],
            "arguments": [],
            "text": message.content,
        }
        if function_calls := message.tool_calls if message.tool_calls else None:
            output = {
                "func_names": [f.function.name for f in function_calls],
                "arguments": [loads(f.function.arguments) for f in function_calls],
            }
        return output

    def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """
        Get a streaming response from an LLM model from OpenAI.

        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        Returns:
            Generator[str, None, None]: A generator that yields the response from the LLM model.
        """
        for delta in self._client.chat.completions.create(
            model=self.model, messages=chat_history, stream=True, **kwargs
        ):
            if not delta.choices:
                continue
            last_content = delta.choices[0].delta.content or ""
            yield last_content
