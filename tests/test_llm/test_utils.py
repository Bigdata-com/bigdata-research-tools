import pytest
from unittest.mock import MagicMock, AsyncMock
from bigdata_research_tools.llm.utils import run_concurrent_prompts

class DummyAsyncLLMEngine:
    async def get_response(self, chat_history, **kwargs):
        return "dummy response"

def test_run_concurrent_prompts(monkeypatch):
    engine = DummyAsyncLLMEngine()
    prompts = ["prompt1", "prompt2"]
    system_prompt = "system"
    responses = run_concurrent_prompts(engine, prompts, system_prompt)
    assert responses == ["dummy response", "dummy response"]
