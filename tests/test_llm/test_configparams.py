import pytest

from bigdata_research_tools.llm.base import (
    LLMProvider,
)


class DummyLLMProviderWithConfig(LLMProvider):
    def __init__(self, model: str | None = None, **connection_config):
        super().__init__(model, **connection_config)
        self.configured = False
        self.connection_params = {}
        self.configure_connection(**self.connection_config)

    def configure_connection(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
        **kwargs,
    ):
        """Mock configure function that requires connection parameters"""
        if not api_key:
            raise ValueError("api_key is required")
        if not base_url:
            raise ValueError("base_url is required")

        self.connection_params.update(
            {
                "api_key": api_key,
                "base_url": base_url,
                "timeout": timeout,
            }
        )
        self.configured = True

    async def get_response(self, chat_history, **kwargs):
        if not self.configured:
            raise RuntimeError(
                "Provider not configured. Call configure_connection first."
            )
        return f"dummy response with api_key: {self.connection_params['api_key']}"

    async def get_tools_response(self, chat_history, tools, temperature=0, **kwargs):
        return {
            "func_names": ["dummy_func"],
            "arguments": [{"api_key": self.connection_params["api_key"]}],
            "text": "dummy text",
        }

    async def get_stream_response(self, chat_history, **kwargs):
        for chunk in ["chunk1", "chunk2"]:
            yield f"{chunk}_with_key_{self.connection_params['api_key']}"


class DummyLLMProviderWithConfigNonRequiredParams(LLMProvider):
    def __init__(self, model: str | None = None, **connection_config):
        super().__init__(model, **connection_config)
        self.configured = False
        self.connection_params = {}
        self.configure_connection(**self.connection_config)

    def configure_connection(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
        **kwargs,
    ):
        """Mock configure function that requires connection parameters"""

        self.configured = True

    async def get_response(self, chat_history, **kwargs):
        if not self.configured:
            raise RuntimeError(
                "Provider not configured. Call configure_connection first."
            )
        return f"dummy response with api_key: {self.connection_params['api_key']}"

    async def get_tools_response(self, chat_history, tools, temperature=0, **kwargs):
        return {
            "func_names": ["dummy_func"],
            "arguments": [{"api_key": self.connection_params["api_key"]}],
            "text": "dummy text",
        }

    async def get_stream_response(self, chat_history, **kwargs):
        for chunk in ["chunk1", "chunk2"]:
            yield f"{chunk}_with_key_{self.connection_params['api_key']}"


class TestConnectionConfig:
    def test_dummy_provider_initialization_with_config(self):
        """Test that DummyLLMProvider can be initialized with connection config and auto-configured"""
        config = {
            "api_key": "test_key_123",
            "base_url": "https://api.example.com",
            "timeout": 60,
        }

        provider = DummyLLMProviderWithConfig(model="test-model", **config)

        assert provider.model == "test-model"
        assert provider.connection_config == config
        assert (
            provider.configured
        )  # Should be auto-configured when valid config is provided
        assert provider.connection_params["api_key"] == "test_key_123"
        assert provider.connection_params["base_url"] == "https://api.example.com"
        assert provider.connection_params["timeout"] == 60

    def test_configure_connection_missing_keyword_parameter(self):
        """Test configure_connection raises error when one required config parameter is missing"""

        with pytest.raises(ValueError, match="api_key is required"):
            _ = DummyLLMProviderWithConfig(model="test-model")

    def test_connection_config_passed_through_init(self):
        """Test that connection_config parameters are accessible through init and auto-configured"""
        config = {
            "api_key": "init_key_xyz",
            "base_url": "https://init.api.com",
            "timeout": 120,
            "extra_param": "extra_value",
        }

        provider = DummyLLMProviderWithConfig(model="test-model", **config)

        # Verify all config parameters are stored
        assert provider.connection_config["api_key"] == "init_key_xyz"
        assert provider.connection_config["base_url"] == "https://init.api.com"
        assert provider.connection_config["timeout"] == 120
        assert provider.connection_config["extra_param"] == "extra_value"
        assert provider.configured

    def test_auto_configuration_failure_handling(self):
        """Test that auto-configuration failures are handled gracefully"""
        config = {
            "api_key": "",  # Invalid empty api_key
            "base_url": "https://api.example.com",
        }

        # This should raise an error during initialization due to invalid api_key
        with pytest.raises(ValueError, match="api_key is required"):
            DummyLLMProviderWithConfig(model="test-model", **config)

    def test_dummy_provider_initialization_with_non_required_config(self):
        """Test that DummyLLMProvider can be initialized with connection config and auto-configured even if no required params"""

        provider = DummyLLMProviderWithConfigNonRequiredParams(model="test-model")

        assert provider.model == "test-model"
        assert provider.connection_config == {}
        assert (
            provider.configured
        )  # Should be auto-configured when valid config is provided
