"""LLM client using OpenAI."""

import json
import os
import re
from typing import Any, Generator, TypeVar

from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

# Type alias for chat messages (compatible with OpenAI API)
ChatMessage = dict[str, Any]


class LLMClient:
    """LLM client for OpenAI models."""

    STRUCTURED_OUTPUT_MODELS = {"gpt-4o-mini", "gpt-4o"}

    def __init__(self, api_key: str | None = None):
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        logger.debug(f"LLMClient initialized: {self.model_name}")

    def _build_messages(
        self, system_prompt: str, data: dict[str, str]
    ) -> list[ChatMessage]:
        """Build messages array from system prompt and data."""
        parts = [f"<{k}>\n{v}\n</{k}>" for k, v in data.items()]
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(parts)},
        ]

    def call_api(
        self,
        system_prompt: str,
        data: dict[str, str],
    ) -> str:
        """Make a non-streaming API call."""
        messages = self._build_messages(system_prompt, data)

        logger.info(f"LLM call | model={self.model_name}")
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("No content returned from LLM")
        return content

    def call_api_stream(
        self,
        system_prompt: str,
        data: dict[str, str],
    ) -> Generator[str, None, None]:
        """Make a streaming API call."""
        messages = self._build_messages(system_prompt, data)

        logger.info(f"LLM stream | model={self.model_name}")
        stream = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def call_api_structured(
        self,
        system_prompt: str,
        data: dict[str, str],
        response_model: type[T],
    ) -> T:
        """Make an API call expecting structured JSON response."""
        schema = response_model.model_json_schema()
        messages = self._build_messages(system_prompt, data)

        if self.model_name in self.STRUCTURED_OUTPUT_MODELS:
            logger.info(f"LLM structured | model={self.model_name}")
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "strict": False,
                        "schema": schema,
                    },
                },
            )
            content = response.choices[0].message.content
        else:
            # Add schema to system prompt for non-structured models
            schema_suffix = f"\n\nRespond with valid JSON matching this schema:\n```json\n{json.dumps(schema, indent=2)}\n```"
            messages = [
                {
                    "role": "system",
                    "content": str(messages[0]["content"]) + schema_suffix,
                },
                messages[1],
            ]
            logger.info(f"LLM structured | model={self.model_name}")
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("No content returned from LLM")
            content = self._extract_json(raw_content)

        if not content:
            raise ValueError("No content returned from LLM")

        try:
            return response_model.model_validate_json(content)
        except ValidationError as e:
            logger.error(f"Parse failed: {e}")
            raise ValueError(f"Invalid response format: {e}")

    def _extract_json(self, content: str) -> str:
        """Extract JSON from markdown code blocks or raw text."""
        # Try code blocks first
        if match := re.search(r"```(?:json)?\s*([\s\S]*?)```", content):
            return match.group(1).strip()

        # Find raw JSON object
        if "{" in content:
            start = content.find("{")
            depth = 0
            for i, c in enumerate(content[start:], start):
                depth += (c == "{") - (c == "}")
                if depth == 0:
                    return content[start : i + 1]

        return content.strip()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    client = LLMClient()
    print(f"Model: {client.model_name}")

    response = client.call_api(
        system_prompt="You are a helpful assistant.",
        data={"question": "What is 2 + 2?"},
    )
    print(f"Response: {response}")
