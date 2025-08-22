from os import environ
from typing import Any, Generator

try:
    from boto3 import Session
except ImportError:
    raise ImportError(
        "Missing optional dependency for LLM Bedrock provider, "
        "please install `bigdata_research_tools[bedrock]` to enable them."
    )

from bigdata_research_tools.llm.base import AsyncLLMProvider, LLMProvider


class AsyncBedrockProvider(AsyncLLMProvider):
    # Asynchronous boto3 is tricky, for now use the synchronous client, this will not 
    # provide the benefits from async, but will at least let our workflows run for now
    def __init__(self, model: str, region: str = None):
        super().__init__(model)
        self.region: str = region
        self._client: Session = None
        self.configure_bedrock_client()

    def configure_bedrock_client(self) -> None:
        """
        Implement a singleton pattern for the Bedrock client, as an AWS
        Boto3 Session.
        Delays the creation of the client until it's needed to facilitate
        loading the environment.
        """
        if not self._client:
            self._client = Session(
                region_name=self.region or environ.get("AWS_DEFAULT_REGION")
            )

    def _get_bedrock_input(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> tuple[Session, dict[str, Any], str]:
        """
        Get the input for the Bedrock API.
        :param chat_history: the chat history to get the input from.
        """
        bedrock_client = self._client.client("bedrock-runtime")
        default_kwargs = {
            "temperature": 0.01,
            "max_tokens": 2048,
            "low_latency": False,
        }
        kwargs = {**default_kwargs, **kwargs}
        formatted_history = []
        system = []
        response_prefix = ""
        for message in chat_history:
            if message["role"] != "system":
                formatted_history.append({"role": message["role"], "content": [{"text": message["content"]}]})
            else:
                system.append({"text": message["content"]})
        if "response_format" in kwargs and kwargs["response_format"].get("type") == "json":
            formatted_history.append(
                {"role": "assistant", "content": [{"text": "{"}]}
            )
            response_prefix = "{"
        # https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
        model_kwargs = {
            "modelId": self.model,
            "messages": formatted_history,
            "system": system,
            "inferenceConfig": {
                "temperature": kwargs.get("temperature"),
                "maxTokens": kwargs.get("max_tokens"),
            },
            "performanceConfig": {
                "latency": "optimized" if kwargs.get("low_latency") else "standard"
            },
        }
        return bedrock_client, model_kwargs, response_prefix

    async def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """
        Get the response from an LLM model from OpenAI.

        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            kwargs (dict): Additional arguments to pass to the Bedrock API:
                - temperature (float): Temperature for the model. Default to 0.01.
                - max_tokens (int): Max tokens for the response of the model. Default to 2048.
                - low_latency (bool): If True, will use the optimized latency. Default to False.
                    Only implemented for a few models. See
                    https://docs.aws.amazon.com/bedrock/latest/userguide/latency-optimized-inference.html
        """
        bedrock_client, model_kwargs, output_prefix = self._get_bedrock_input(chat_history, **kwargs)
        response = bedrock_client.converse(**model_kwargs)

        output_message = (
            response.get("output", {}).get("message", {}).get("content", {})
        )
        text = "".join([x["text"] for x in output_message if "text" in x])
        return output_prefix + text

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
        bedrock_client, model_kwargs, output_prefix = self._get_bedrock_input(chat_history, **kwargs)
        if tools:
            model_kwargs["toolConfig"] = {"tools": tools}
        response = bedrock_client.converse(**model_kwargs)

        output_message = (
            response.get("output", {}).get("message", {}).get("content", {})
        )
        output = {
            # Bedrock also returns a field "text" when using tools,
            # explaining what the model thought about using the selected tools
            "func_names": [
                f.get("toolUse", {}).get("name")
                for f in output_message
                if "text" not in f
            ],
            "arguments": [
                f.get("toolUse", {}).get("input")
                for f in output_message
                if "text" not in f
            ],
            "text": output_prefix + "".join([x["text"] for x in output_message if "text" in x]),
        }
        return output

    async def get_stream_response(
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
        raise NotImplementedError

class BedrockProvider(LLMProvider):
    def __init__(self, model: str, region: str = None):
        super().__init__(model)
        self.region: str = region
        self._client: Session = None
        self.configure_bedrock_client()

    def configure_bedrock_client(self) -> None:
        """
        Implement a singleton pattern for the Bedrock client, as an AWS
        Boto3 Session.
        Delays the creation of the client until it's needed to facilitate
        loading the environment.
        """
        if not self._client:
            self._client = Session(
                region_name=self.region or environ.get("AWS_DEFAULT_REGION")
            )

    def _get_bedrock_input(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> tuple[Session, dict[str, Any]]:
        """
        Get the input for the Bedrock API.
        :param chat_history: the chat history to get the input from.
        """
        bedrock_client = self._client.client("bedrock-runtime")
        default_kwargs = {
            "temperature": 0.01,
            "max_tokens": 2048,
            "low_latency": False,
        }
        kwargs = {**default_kwargs, **kwargs}
        formatted_history = []
        system = []
        response_prefix = ""
        for message in chat_history:
            if message["role"] != "system":
                formatted_history.append({"role": message["role"], "content": [{"text": message["content"]}]})
            else:
                system.append({"text": message["content"]})
        if "response_format" in kwargs and kwargs["response_format"].get("type") == "json":
            formatted_history.append(
                {"role": "assistant", "content": [{"text": "{"}]}
            )
            response_prefix = "{"
        # https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
        model_kwargs = {
            "modelId": self.model,
            "messages": formatted_history,
            "system": system,
            "inferenceConfig": {
                "temperature": kwargs.get("temperature"),
                "maxTokens": kwargs.get("max_tokens"),
            },
            "performanceConfig": {
                "latency": "optimized" if kwargs.get("low_latency") else "standard"
            },
        }
        return bedrock_client, model_kwargs, response_prefix

    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """
        Get the response from an LLM model from OpenAI.

        Args:
            chat_history (list[dict[str, str]]): List of messages, each including at least:
                - role: the role of the messenger (either system, user, assistant or tool)
                - content: the content of the message (e.g., Write me a beautiful poem)
                Reference examples of the format accepted: https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            kwargs (dict): Additional arguments to pass to the Bedrock API:
                - temperature (float): Temperature for the model. Default to 0.01.
                - max_tokens (int): Max tokens for the response of the model. Default to 2048.
                - low_latency (bool): If True, will use the optimized latency. Default to False.
                    Only implemented for a few models. See
                    https://docs.aws.amazon.com/bedrock/latest/userguide/latency-optimized-inference.html
        """
        bedrock_client, model_kwargs, output_prefix = self._get_bedrock_input(chat_history, **kwargs)
        response = bedrock_client.converse(**model_kwargs)

        output_message = (
            response.get("output", {}).get("message", {}).get("content", {})
        )
        text = "".join([x["text"] for x in output_message if "text" in x])
        return output_prefix + text

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
        bedrock_client, model_kwargs, output_prefix = self._get_bedrock_input(chat_history, **kwargs)
        if tools:
            model_kwargs["toolConfig"] = {"tools": tools}
        response = bedrock_client.converse(**model_kwargs)

        output_message = (
            response.get("output", {}).get("message", {}).get("content", {})
        )
        output = {
            # Bedrock also returns a field "text" when using tools,
            # explaining what the model thought about using the selected tools
            "func_names": [
                f.get("toolUse", {}).get("name")
                for f in output_message
                if "text" not in f
            ],
            "arguments": [
                f.get("toolUse", {}).get("input")
                for f in output_message
                if "text" not in f
            ],
            "text": output_prefix + "".join([x["text"] for x in output_message if "text" in x]),
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
        raise NotImplementedError
