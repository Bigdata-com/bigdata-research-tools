import os
from abc import ABC, abstractmethod
from logging import Logger, getLogger

logger: Logger = getLogger(__name__)


class AsyncEmbeddingsProvider(ABC):
    def __init__(self, model: str = None):
        self.model = model

    @abstractmethod
    async def get_embeddings(self, text: str) -> list[float]:
        """
        Get the embedding of a text using an LLM model.
        """
        pass


class AsyncEmbeddingsEngine:
    def __init__(self, model: str = None):
        if model is None:
            model = os.getenv("BIGDATA_RESEARCH_DEFAULT_EMBEDDINGS")
            source = "Environment"
        else:
            source = "Argument"

        try:
            self.provider, self.model = model.split("::")
        except (ValueError, AttributeError):
            logger.error(
                f"Invalid embeddings model format. It should be "
                f"`<provider>::<model>`.\nModel: {model}. "
                f"Source: {source}",
            )

            raise ValueError(
                "Invalid embeddings model format. It should be `<provider>::<model>`."
            )

        self.provider = self.load_provider()

    def load_provider(self) -> AsyncEmbeddingsProvider:
        provider = self.provider.lower()
        if provider == "openai":
            from bigdata_research_tools.embeddings.openai import AsyncOpenAIEmbeddings

            return AsyncOpenAIEmbeddings(model=self.model)
        elif provider == "bedrock":
            raise NotImplementedError
            # from bigdata_research_tools.llm.bedrock import BedrockProvider
            #
            # return BedrockProvider(
            #     model=self.model, embeddings_model=self.embeddings_model
            # )
        else:
            logger.error(f"Invalid provider: `{self.provider}`")

            raise ValueError("Invalid provider")

    async def get_embeddings(self, text: str) -> list[float]:
        return await self.provider.get_embeddings(text)


class EmbeddingsProvider(ABC):
    def __init__(self, model: str = None):
        self.model = model

    @abstractmethod
    def get_embeddings(self, text: str) -> list[float]:
        """
        Get the embedding of a text using an LLM model.
        """
        pass


class EmbeddingsEngine:
    def __init__(self, model: str = None):
        if model is None:
            model = os.getenv("BIGDATA_RESEARCH_DEFAULT_EMBEDDINGS")
            source = "Environment"
        else:
            source = "Argument"

        try:
            self.provider, self.model = model.split("::")
        except (ValueError, AttributeError):
            logger.error(
                f"Invalid embeddings model format. It should be "
                f"`<provider>::<model>`.\nModel: {model}. "
                f"Source: {source}",
            )

            raise ValueError(
                "Invalid embeddings model format. It should be `<provider>::<model>`."
            )

        self.provider = self.load_provider()

    def load_provider(self) -> EmbeddingsProvider:
        provider = self.provider.lower()
        if provider == "openai":
            from bigdata_research_tools.embeddings.openai import OpenAIEmbeddings

            return OpenAIEmbeddings(model=self.model)
        elif provider == "bedrock":
            raise NotImplementedError
            # from bigdata_research_tools.llm.bedrock import BedrockProvider
            #
            # return BedrockProvider(
            #     model=self.model, embeddings_model=self.embeddings_model
            # )
        else:
            logger.error(f"Invalid provider: `{self.provider}`")

            raise ValueError("Invalid provider")

    def get_embeddings(self, text: str) -> list[float]:
        return self.provider.get_embeddings(text)
