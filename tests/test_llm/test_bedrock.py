
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from bigdata_research_tools.llm.bedrock import AsyncBedrockProvider

@pytest.mark.asyncio
@patch('bigdata_research_tools.llm.bedrock.Session')
async def test_get_response(mock_session):
    mock_bedrock_client = MagicMock()
    mock_bedrock_client.converse.return_value = {
        "output": {"message": {"content": [{"text": "mocked bedrock response"}]}}
    }
    mock_session.return_value = MagicMock(client=MagicMock(return_value=mock_bedrock_client))
    provider = AsyncBedrockProvider(model="bedrock-model", region="us-east-1")
    chat_history = [{"role": "user", "content": "Hello"}]
    response = await provider.get_response(chat_history)
    assert response == "mocked bedrock response"

@pytest.mark.asyncio
@patch('bigdata_research_tools.llm.bedrock.Session')
async def test_get_tools_response(mock_session):
    mock_bedrock_client = MagicMock()
    mock_bedrock_client.converse.return_value = {
        "output": {"message": {"content": [
            {"toolUse": {"name": "tool1", "input": {"arg": "val"}}},
            {"text": "tool response text"}
        ]}}
    }
    mock_session.return_value = MagicMock(client=MagicMock(return_value=mock_bedrock_client))
    provider = AsyncBedrockProvider(model="bedrock-model", region="us-east-1")
    chat_history = [{"role": "user", "content": "Use tool"}]
    tools = [{"name": "tool1"}]
    response = await provider.get_tools_response(chat_history, tools)
    assert isinstance(response, dict)
    assert response["func_names"] == ["tool1"]
    assert response["arguments"] == [{"arg": "val"}]

@pytest.mark.asyncio
@patch('bigdata_research_tools.llm.bedrock.Session')
async def test_get_stream_response_not_implemented(mock_session):
    provider = AsyncBedrockProvider(model="bedrock-model", region="us-east-1")
    chat_history = [{"role": "user", "content": "Stream"}]
    with pytest.raises(NotImplementedError):
        await provider.get_stream_response(chat_history)