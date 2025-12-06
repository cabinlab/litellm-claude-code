import asyncio
from typing import Dict, List, Iterator, AsyncIterator, Any
import litellm
from litellm import CustomLLM, ModelResponse, Usage
from litellm.types.utils import Choices, Message as LiteLLMMessage, GenericStreamingChunk, Delta

from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk.types import AssistantMessage, TextBlock

class ClaudeCodeSDKProvider(CustomLLM):
    """LiteLLM provider for Claude Code SDK with proper model selection."""
    
    def __init__(self):
        super().__init__()
        print("ClaudeCodeSDKProvider initialized")
    
    def format_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert LiteLLM messages to Claude prompt."""
        prompt_parts = []
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def extract_claude_model(self, model: str) -> str:
        """Extract Claude model name from LiteLLM model parameter."""
        # Handle "claude-code-sdk/claude-3-5-sonnet" -> "claude-3-5-sonnet"
        # Or just "claude-3-5-sonnet" -> "claude-3-5-sonnet"
        return model.split('/')[-1] if '/' in model else model
    
    def create_litellm_response(self, content: str, model: str) -> ModelResponse:
        """Convert Claude response to LiteLLM format."""
        import uuid
        from datetime import datetime
        
        message = LiteLLMMessage(content=content, role="assistant")
        choice = Choices(finish_reason="stop", index=0, message=message)
        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        
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
        """Async completion using Claude Code SDK with model selection."""
        prompt = self.format_messages_to_prompt(messages)
        claude_model = self.extract_claude_model(model)
        
        # Create options with proper model selection
        options = ClaudeCodeOptions(model=claude_model)
        
        response_content = ""
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_content += block.text
        
        return self.create_litellm_response(response_content, model)
    
    def streaming(self, model: str, messages: List[Dict], **kwargs) -> Iterator[GenericStreamingChunk]:
        """Sync streaming - not supported, will raise error."""
        raise NotImplementedError("Sync streaming is not supported. Use async streaming instead.")
    
    async def astreaming(self, model: str, messages: List[Dict], **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """Async streaming using Claude Code SDK."""
        prompt = self.format_messages_to_prompt(messages)
        claude_model = self.extract_claude_model(model)
        
        # Create options with proper model selection
        options = ClaudeCodeOptions(model=claude_model)
        
        total_content = ""
        
        async for message in query(prompt=prompt, options=options):
            # Only process AssistantMessage with TextBlock content
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        content = block.text
                        total_content += content
                        
                        # Yield content as provided by Claude Code SDK
                        chunk: GenericStreamingChunk = {
                            "text": content,
                            "is_finished": False,
                            "finish_reason": None,
                            "index": 0,
                            "tool_use": None,
                            "usage": None
                        }
                        yield chunk
        
        # Send final chunk with finish_reason
        final_chunk: GenericStreamingChunk = {
            "text": "",
            "is_finished": True,
            "finish_reason": "stop",
            "index": 0,
            "tool_use": None,
            "usage": {
                "completion_tokens": len(total_content.split()),
                "prompt_tokens": 100,
                "total_tokens": 100 + len(total_content.split())
            }
        }
        
        yield final_chunk

# Register provider
def register_provider():
    claude_provider = ClaudeCodeSDKProvider()
    
    if not hasattr(litellm, 'custom_provider_map'):
        litellm.custom_provider_map = []
    
    litellm.custom_provider_map.append({
        "provider": "claude-code-sdk",
        "custom_handler": claude_provider
    })
    
    print(f"Registered custom provider: {litellm.custom_provider_map}")

register_provider()

# Create provider instance for YAML config
provider_instance = ClaudeCodeSDKProvider()