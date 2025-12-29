"""LLM client using LangChain with OpenAI."""

import os
from typing import Any, Generator, TypeVar, cast

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

# Type alias for chat messages (compatible with OpenAI API)
ChatMessage = dict[str, Any]


class LLMClient:
    """LLM client using LangChain abstractions."""

    def __init__(self, api_key: str | None = None):
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = ChatOpenAI(
            model=self.model_name,  # type: ignore[call-arg]
            temperature=0,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),  # type: ignore[call-arg]
        )
        logger.debug(f"LLMClient initialized: {self.model_name}")

    def _build_prompt(
        self, system_prompt: str, data: dict[str, str]
    ) -> ChatPromptTemplate:
        """Build a ChatPromptTemplate from system prompt and data."""
        parts = [f"<{k}>\n{{{k}}}\n</{k}>" for k in data.keys()]
        user_template = "\n\n".join(parts)
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_template),
            ]
        )

    def call_api(
        self,
        system_prompt: str,
        data: dict[str, str],
    ) -> str:
        """Make a non-streaming API call."""
        prompt = self._build_prompt(system_prompt, data)
        chain = prompt | self._client

        logger.info(f"LLM call | model={self.model_name}")
        response = chain.invoke(data)

        content = response.content
        if not content:
            raise ValueError("No content returned from LLM")
        return str(content)

    def call_api_stream(
        self,
        system_prompt: str,
        data: dict[str, str],
    ) -> Generator[str, None, None]:
        """Make a streaming API call."""
        prompt = self._build_prompt(system_prompt, data)
        chain = prompt | self._client

        logger.info(f"LLM stream | model={self.model_name}")
        for chunk in chain.stream(data):
            if chunk.content:
                yield str(chunk.content)

    def call_api_structured(
        self,
        system_prompt: str,
        data: dict[str, str],
        response_model: type[T],
    ) -> T:
        """Make an API call expecting structured JSON response."""
        prompt = self._build_prompt(system_prompt, data)
        structured_llm = self._client.with_structured_output(response_model)
        chain = prompt | structured_llm

        logger.info(f"LLM structured | model={self.model_name}")
        try:
            response = chain.invoke(data)
            if response is None:
                raise ValueError("No content returned from LLM")
            return cast(T, response)
        except ValidationError as e:
            logger.error(f"Parse failed: {e}")
            raise ValueError(f"Invalid response format: {e}")


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
