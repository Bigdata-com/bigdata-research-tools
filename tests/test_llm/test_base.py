import pytest
from unittest.mock import AsyncMock
from bigdata_research_tools.llm.base import AsyncLLMProvider

class DummyAsyncLLMProvider(AsyncLLMProvider):
    async def get_response(self, chat_history, **kwargs):
        return "dummy response"
    async def get_tools_response(self, chat_history, tools, temperature=0, **kwargs):
        return {"func_names": ["dummy_func"], "arguments": [{}], "text": "dummy text"}
    async def get_stream_response(self, chat_history, **kwargs):
        for chunk in ["chunk1", "chunk2"]:
            yield chunk

@pytest.mark.asyncio
async def test_get_response():
    provider = DummyAsyncLLMProvider(model="dummy-model")
    chat_history = [{"role": "user", "content": "Hi"}]
    response = await provider.get_response(chat_history)
    assert response == "dummy response"

@pytest.mark.asyncio
async def test_get_tools_response():
    provider = DummyAsyncLLMProvider(model="dummy-model")
    chat_history = [{"role": "user", "content": "Tool"}]
    tools = [{"name": "tool1"}]
    response = await provider.get_tools_response(chat_history, tools)
    assert response["func_names"] == ["dummy_func"]
    assert response["text"] == "dummy text"

@pytest.mark.asyncio
async def test_get_stream_response():
    provider = DummyAsyncLLMProvider(model="dummy-model")
    chat_history = [{"role": "user", "content": "Stream"}]
    result = []
    async for chunk in provider.get_stream_response(chat_history):
        result.append(chunk)
    assert result == ["chunk1", "chunk2"]
