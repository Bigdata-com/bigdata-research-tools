from __future__ import annotations

from json import loads
from typing import AsyncGenerator, Generator

try:
    from openai import AsyncOpenAI, OpenAI
except ImportError:
    raise ImportError(
        "Missing optional dependency for LLM OpenAI provider, "
        "please install `bigdata_research_tools[openai]` to enable them."
    )

from bigdata_research_tools.llm.base import AsyncLLMProvider, LLMProvider


class AsyncOpenAIProvider(AsyncLLMProvider):
    def __init__(
        self,
        model: str,
    ):
        super().__init__(model)
        self._client = None
        self.configure_openai_client()

    def configure_openai_client(self) -> None:
        """
        Implement a singleton pattern for the OpenAI client.
        Delays the creation of the client until it's needed to facilitate
        loading the environment.

        Returns:
            OpenAI: The OpenAI client.
        """
        if not self._client:
            self._client = AsyncOpenAI()

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
        chat_completion = await self._client.chat.completions.create(
            messages=chat_history, model=self.model, **kwargs
        )

        return chat_completion.choices[0].message.content

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
            last_content = delta.choices[0].delta.content or ""
            yield last_content


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        model: str,
    ):
        super().__init__(model)
        self._client = None
        self.configure_openai_client()

    def configure_openai_client(self) -> None:
        """
        Implement a singleton pattern for the OpenAI client.
        Delays the creation of the client until it's needed to facilitate
        loading the environment.

        Returns:
            OpenAI: The OpenAI client.
        """
        if not self._client:
            self._client = OpenAI()

    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """
        Get the response from an LLM model from OpenAI.

        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            kwargs (dict): Additional arguments to pass to the OpenAI API.
        """
        chat_completion = self._client.chat.completions.create(
            messages=chat_history, model=self.model, **kwargs
        )

        return chat_completion.choices[0].message.content

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
            last_content = delta.choices[0].delta.content or ""
            yield last_content
