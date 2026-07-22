from openai import AsyncOpenAI

from legal_graph.core.errors import AppError


class OpenAIEmbeddingProvider:
    def __init__(self, api_key: str, model: str, dimensions: int, timeout_seconds: float) -> None:
        self.model = model
        self.dimensions = dimensions
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)

    async def embed(self, text: str) -> list[float]:
        try:
            response = await self._client.embeddings.create(
                model=self.model, dimensions=self.dimensions, input=text
            )
        except Exception as error:
            raise AppError(
                "MODEL_UNAVAILABLE",
                "Embedding provider is unavailable",
                status_code=503,
                retryable=True,
            ) from error
        vector = response.data[0].embedding
        if len(vector) != self.dimensions:
            raise AppError(
                "EMBEDDING_MODEL_MISMATCH",
                "Embedding dimensions do not match configured vector indexes",
                status_code=409,
            )
        return vector

    async def health(self) -> bool:
        # Configuration presence is enough for the lightweight health endpoint.
        return bool(self._client.api_key and self.model and self.dimensions)

    async def close(self) -> None:
        await self._client.close()
