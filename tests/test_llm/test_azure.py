from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bigdata_research_tools.llm.azure import AsyncAzureProvider


@pytest.mark.asyncio
@patch("bigdata_research_tools.llm.azure.AsyncAzureOpenAI")
async def test_get_response(mock_async_azure):
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="mocked response"))]
    )
    mock_async_azure.return_value = mock_client
    provider = AsyncAzureProvider(model="gpt-4o-mini")
    chat_history = [{"role": "user", "content": "Hello"}]
    response = await provider.get_response(chat_history)
    assert response == "mocked response"


@pytest.mark.asyncio
@patch("bigdata_research_tools.llm.azure.AsyncAzureOpenAI")
async def test_get_tools_response(mock_async_azure):
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="tool response"))]
    )
    mock_async_azure.return_value = mock_client
    provider = AsyncAzureProvider(model="gpt-4o-mini")
    chat_history = [{"role": "user", "content": "Use tool"}]
    tools = [{"name": "tool1"}]
    response = await provider.get_tools_response(chat_history, tools)
    assert isinstance(response, dict)


@pytest.mark.asyncio
@patch("bigdata_research_tools.llm.azure.AsyncAzureOpenAI")
async def test_get_stream_response(mock_async_azure):
    mock_client = AsyncMock()
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="streamed"))])
    ]
    mock_client.chat.completions.create.return_value = mock_stream
    mock_async_azure.return_value = mock_client
    provider = AsyncAzureProvider(model="gpt-4o-mini")
    chat_history = [{"role": "user", "content": "Stream"}]
    result = []
    async for chunk in provider.get_stream_response(chat_history):
        result.append(chunk)
    assert result == ["streamed"]
