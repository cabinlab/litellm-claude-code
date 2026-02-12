import asyncio
import concurrent.futures
import time
import uuid
from typing import AsyncIterator, Dict, Iterator, List, Tuple

import litellm
from litellm import CustomLLM, ModelResponse, Usage
from litellm.types.utils import Choices, GenericStreamingChunk, Message as LiteLLMMessage

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."

ROLE_PREFIXES = {"user": "Human", "assistant": "Assistant"}


class ClaudeAgentSDKProvider(CustomLLM):
    """LiteLLM provider that wraps the Claude Agent SDK as a plain model call."""

    def __init__(self):
        super().__init__()
        print("ClaudeAgentSDKProvider initialized")

    @staticmethod
    def _split_messages(messages: List[Dict]) -> Tuple[str, str]:
        """Separate system prompt from conversation turns.

        Returns (system_prompt, conversation_prompt).
        """
        system_parts = []
        turn_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_parts.append(content)
            else:
                prefix = ROLE_PREFIXES.get(role)
                if prefix:
                    turn_parts.append(f"{prefix}: {content}")

        system_prompt = "\n\n".join(system_parts) if system_parts else DEFAULT_SYSTEM_PROMPT
        conversation = "\n\n".join(turn_parts)
        return system_prompt, conversation

    @staticmethod
    def _extract_model(model: str) -> str:
        """Strip the 'claude-agent-sdk/' prefix if present."""
        return model.split("/")[-1] if "/" in model else model

    @staticmethod
    def _extract_usage(usage_data) -> Tuple[int, int]:
        """Parse token counts from a Claude Agent SDK usage object or dict."""
        if isinstance(usage_data, dict):
            prompt = usage_data.get("input_tokens", 0) or 0
            completion = usage_data.get("output_tokens", 0) or 0
        else:
            prompt = getattr(usage_data, "input_tokens", 0) or 0
            completion = getattr(usage_data, "output_tokens", 0) or 0
        return prompt, completion

    def _build_response(
        self, content: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0
    ) -> ModelResponse:
        """Build an OpenAI-compatible ModelResponse."""
        response = ModelResponse()
        response.id = f"chatcmpl-{uuid.uuid4().hex}"
        response.object = "chat.completion"
        response.created = int(time.time())
        response.model = model
        response.choices = [
            Choices(
                finish_reason="stop",
                index=0,
                message=LiteLLMMessage(content=content, role="assistant"),
            )
        ]
        response.usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        return response

    def completion(self, model: str, messages: List[Dict], **kwargs) -> ModelResponse:
        """Sync completion -- delegates to acompletion via a thread if needed."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run, self.acompletion(model, messages, **kwargs)
                ).result()

        return asyncio.run(self.acompletion(model, messages, **kwargs))

    async def acompletion(self, model: str, messages: List[Dict], **kwargs) -> ModelResponse:
        """Async completion using Claude Agent SDK."""
        system_prompt, prompt = self._split_messages(messages)
        options = ClaudeAgentOptions(
            model=self._extract_model(model),
            system_prompt=system_prompt,
            allowed_tools=[],
            max_turns=1,
        )

        content = ""
        prompt_tokens = 0
        completion_tokens = 0

        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            content += block.text
                elif isinstance(message, ResultMessage) and getattr(message, "usage", None):
                    prompt_tokens, completion_tokens = self._extract_usage(message.usage)
        except Exception as e:
            raise litellm.exceptions.APIError(
                status_code=500,
                message=f"Claude Agent SDK query failed: {e}",
                model=model,
                llm_provider="claude-agent-sdk",
            )

        return self._build_response(content, model, prompt_tokens, completion_tokens)

    def streaming(self, model: str, messages: List[Dict], **kwargs) -> Iterator[GenericStreamingChunk]:
        raise NotImplementedError("Sync streaming is not supported. Use async streaming instead.")

    async def astreaming(self, model: str, messages: List[Dict], **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """Async streaming using Claude Agent SDK."""
        system_prompt, prompt = self._split_messages(messages)
        options = ClaudeAgentOptions(
            model=self._extract_model(model),
            system_prompt=system_prompt,
            allowed_tools=[],
            max_turns=1,
        )

        total_chars = 0
        prompt_tokens = 0
        completion_tokens = 0

        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            total_chars += len(block.text)
                            yield {
                                "text": block.text,
                                "is_finished": False,
                                "finish_reason": None,
                                "index": 0,
                                "tool_use": None,
                                "usage": None,
                            }
                elif isinstance(message, ResultMessage) and getattr(message, "usage", None):
                    prompt_tokens, completion_tokens = self._extract_usage(message.usage)
        except Exception as e:
            raise litellm.exceptions.APIError(
                status_code=500,
                message=f"Claude Agent SDK streaming failed: {e}",
                model=model,
                llm_provider="claude-agent-sdk",
            )

        # Fall back to a rough estimate when the SDK doesn't report usage
        if not prompt_tokens and not completion_tokens:
            completion_tokens = total_chars // 4

        yield {
            "text": "",
            "is_finished": True,
            "finish_reason": "stop",
            "index": 0,
            "tool_use": None,
            "usage": {
                "completion_tokens": completion_tokens,
                "prompt_tokens": prompt_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }


# Module-level instance referenced by litellm_config.yaml custom_provider_map
claude_agent_provider = ClaudeAgentSDKProvider()
