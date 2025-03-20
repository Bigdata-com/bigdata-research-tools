try:
    from openai import AsyncOpenAI, OpenAI
except ImportError:
    raise ImportError(
        "Missing optional dependency for LLM OpenAI provider, "
        "please install `bigdata_research_tools[openai]` to enable them."
    )

from bigdata_research_tools.embeddings.base import (
    AsyncEmbeddingsProvider,
    EmbeddingsProvider,
)

# TODO openai Azure provider - Check if it's possible to implement it


class AsyncOpenAIEmbeddings(AsyncEmbeddingsProvider):
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

    async def get_embeddings(self, text: str) -> list[float]:
        """
        Get the embedding of a text using OpenAI API.
        :param text: the text to get the embedding from.
        """
        text = text.replace("\n", " ")
        return (
            (await self._client.embeddings.create(input=[text], model=self.model))
            .data[0]
            .embedding
        )


class OpenAIEmbeddings(EmbeddingsProvider):
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

    def get_embeddings(self, text: str) -> list[float]:
        """
        Get the embedding of a text using OpenAI API.
        :param text: the text to get the embedding from.
        """
        text = text.replace("\n", " ")
        return (
            (self._client.embeddings.create(input=[text], model=self.model))
            .data[0]
            .embedding
        )
