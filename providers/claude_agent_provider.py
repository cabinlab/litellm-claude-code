import asyncio
from typing import Dict, List, Iterator, AsyncIterator
import uuid
from datetime import datetime

import litellm
from litellm import CustomLLM, ModelResponse, Usage
from litellm.types.utils import Choices, Message as LiteLLMMessage, GenericStreamingChunk

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock


class ClaudeAgentSDKProvider(CustomLLM):
    """LiteLLM provider for Claude Agent SDK with proper model selection."""

    def __init__(self):
        super().__init__()
        print("ClaudeAgentSDKProvider initialized")

    def format_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert LiteLLM messages to Claude prompt."""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)

    def extract_claude_model(self, model: str) -> str:
        """Extract Claude model name from LiteLLM model parameter.

        Handles 'claude-agent-sdk/claude-3-5-sonnet' -> 'claude-3-5-sonnet'
        or just 'claude-3-5-sonnet' -> 'claude-3-5-sonnet'.
        """
        return model.split("/")[-1] if "/" in model else model

    def create_litellm_response(
        self, content: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0
    ) -> ModelResponse:
        """Convert Claude response to LiteLLM format."""
        message = LiteLLMMessage(content=content, role="assistant")
        choice = Choices(finish_reason="stop", index=0, message=message)

        total_tokens = prompt_tokens + completion_tokens
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        response = ModelResponse()
        response.id = f"chatcmpl-{uuid.uuid4().hex}"
        response.object = "chat.completion"
        response.created = int(datetime.now().timestamp())
        response.model = model
        response.choices = [choice]
        response.usage = usage

        return response

    def completion(self, model: str, messages: List[Dict], **kwargs) -> ModelResponse:
        """Sync completion wrapper."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.acompletion(model, messages, **kwargs))
        finally:
            loop.close()

    async def acompletion(self, model: str, messages: List[Dict], **kwargs) -> ModelResponse:
        """Async completion using Claude Agent SDK with model selection."""
        prompt = self.format_messages_to_prompt(messages)
        claude_model = self.extract_claude_model(model)

        options = ClaudeAgentOptions(model=claude_model)

        response_content = ""
        prompt_tokens = 0
        completion_tokens = 0

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_content += block.text
            elif isinstance(message, ResultMessage):
                if hasattr(message, "usage") and message.usage:
                    prompt_tokens = getattr(message.usage, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(message.usage, "completion_tokens", 0) or 0

        return self.create_litellm_response(
            response_content, model, prompt_tokens, completion_tokens
        )

    def streaming(self, model: str, messages: List[Dict], **kwargs) -> Iterator[GenericStreamingChunk]:
        """Sync streaming - not supported."""
        raise NotImplementedError("Sync streaming is not supported. Use async streaming instead.")

    async def astreaming(self, model: str, messages: List[Dict], **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """Async streaming using Claude Agent SDK."""
        prompt = self.format_messages_to_prompt(messages)
        claude_model = self.extract_claude_model(model)

        options = ClaudeAgentOptions(model=claude_model)

        total_content = ""

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        content = block.text
                        total_content += content

                        chunk: GenericStreamingChunk = {
                            "text": content,
                            "is_finished": False,
                            "finish_reason": None,
                            "index": 0,
                            "tool_use": None,
                            "usage": None,
                        }
                        yield chunk

        final_chunk: GenericStreamingChunk = {
            "text": "",
            "is_finished": True,
            "finish_reason": "stop",
            "index": 0,
            "tool_use": None,
            "usage": {
                "completion_tokens": len(total_content.split()),
                "prompt_tokens": 0,
                "total_tokens": len(total_content.split()),
            },
        }

        yield final_chunk


# Module-level provider instance for YAML config reference
claude_agent_provider = ClaudeAgentSDKProvider()
