from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from legal_graph.application.agent_models import ModelUsage
from legal_graph.core.errors import AppError

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


class OpenAIChatProvider:
    def __init__(self, api_key: str, timeout_seconds: float) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[StructuredOutput],
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> tuple[StructuredOutput, ModelUsage]:
        parameters = {
            "model": model,
            "messages": messages,
            "response_format": response_model,
            "max_completion_tokens": max_output_tokens,
        }
        if model.startswith("gpt-5.4"):
            parameters["reasoning_effort"] = "none"
        elif model.startswith("gpt-5"):
            # Older GPT-5 models may spend completion tokens on hidden reasoning.
            parameters["reasoning_effort"] = "minimal"
            parameters["max_completion_tokens"] = max(max_output_tokens, 3000)
        elif not model.startswith(("o1", "o3", "o4")):
            parameters["temperature"] = temperature
        try:
            response = await self._client.beta.chat.completions.parse(**parameters)  # type: ignore[arg-type]
        except Exception as error:
            raise AppError(
                "MODEL_UNAVAILABLE",
                "Answer model is unavailable",
                status_code=503,
                retryable=True,
            ) from error
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise AppError(
                "MODEL_OUTPUT_INVALID", "Answer model returned invalid structured output"
            )
        usage = response.usage
        return parsed, ModelUsage(
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

    async def health(self) -> bool:
        return bool(self._client.api_key)

    async def close(self) -> None:
        await self._client.close()
