"""LLM client abstraction supporting OpenAI API and mock implementations."""

from abc import ABC, abstractmethod
import json
import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    LLMResponseValidationError,
    LLMServiceError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """Abstract interface for LLM client providers."""

    @abstractmethod
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
    ) -> T:
        """Generate structured response conforming to the given Pydantic model schema.

        Args:
            system_prompt: System prompt with persona and safety instructions.
            user_prompt: User prompt containing regulatory requirement and evidence.
            response_schema: Target Pydantic model class for validation.

        Returns:
            Validated instance of response_schema.

        Raises:
            LLMTimeoutError: If request times out.
            LLMServiceError: If provider is unreachable or returns error.
            LLMResponseValidationError: If response does not conform to response_schema.
        """
        pass


class OpenAILLMClient(LLMClient):
    """OpenAI API client implementation using standard HTTP requests."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        timeout_seconds: float = 30.0,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self._api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/")

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
    ) -> T:
        if not self._api_key:
            raise LLMServiceError(
                "Compliance analysis service is temporarily unavailable (LLM API key is not configured)."
            )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        schema_json = response_schema.model_json_schema()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "strict": True,
                    "schema": schema_json,
                },
            },
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            logger.error("LLM request timed out after %s seconds", self.timeout_seconds)
            raise LLMTimeoutError(f"LLM request timed out after {self.timeout_seconds}s") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("LLM provider returned HTTP %s", exc.response.status_code)
            raise LLMServiceError("Compliance analysis service is temporarily unavailable.") from exc
        except httpx.RequestError as exc:
            logger.error("LLM provider connection error: %s", type(exc).__name__)
            raise LLMServiceError("Compliance analysis service is temporarily unavailable.") from exc

        try:
            content = data["choices"][0]["message"]["content"]
            parsed_json = json.loads(content)
            return response_schema.model_validate(parsed_json)
        except (KeyError, IndexError, json.JSONDecodeError, PydanticValidationError) as exc:
            logger.error("Failed to parse/validate LLM response: %s", type(exc).__name__)
            raise LLMResponseValidationError(f"Invalid LLM response: {exc}") from exc


class MockLLMClient(LLMClient):
    """Mock LLM client for deterministic unit and integration tests."""

    def __init__(self, response_provider=None) -> None:
        self.response_provider = response_provider
        self.calls: list[dict] = []

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
    ) -> T:
        self.calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response_schema": response_schema,
        })

        if callable(self.response_provider):
            result = self.response_provider(system_prompt, user_prompt, response_schema)
            if isinstance(result, Exception):
                raise result
            if isinstance(result, response_schema):
                return result
            if isinstance(result, dict):
                return response_schema.model_validate(result)
            if isinstance(result, str):
                return response_schema.model_validate_json(result)

        if isinstance(self.response_provider, Exception):
            raise self.response_provider

        if isinstance(self.response_provider, response_schema):
            return self.response_provider

        if isinstance(self.response_provider, dict):
            return response_schema.model_validate(self.response_provider)

        raise LLMServiceError("Mock response provider not configured")


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    """Factory to instantiate configured LLM client."""
    cfg = settings or get_settings()
    if cfg.llm_provider.lower() == "mock":
        return MockLLMClient()
    return OpenAILLMClient(
        api_key=cfg.effective_llm_api_key,
        model=cfg.llm_model,
        temperature=cfg.llm_temperature,
        timeout_seconds=cfg.llm_timeout_seconds,
    )
