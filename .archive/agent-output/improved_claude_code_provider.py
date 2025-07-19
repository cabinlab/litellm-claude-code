"""
Improved Claude Code SDK Provider for LiteLLM.

This implementation includes all recommended improvements:
- Proper system message handling
- Support for all SDK parameters
- Removed artificial chunk splitting  
- Better error handling
- Token estimation
"""

import asyncio
from typing import Dict, List, Iterator, AsyncIterator, Any, Optional, Tuple
import litellm
from litellm import CustomLLM, ModelResponse, Usage
from litellm.types.utils import Choices, Message as LiteLLMMessage, GenericStreamingChunk

try:
    from claude_code_sdk import query, ClaudeCodeOptions, ClaudeSDKError
    from claude_code_sdk.types import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock
    from claude_code_sdk import (
        CLINotFoundError,
        CLIConnectionError, 
        ProcessError,
        CLIJSONDecodeError
    )
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("WARNING: Claude Code SDK not installed. Install with: pip install claude-code-sdk")


class ImprovedClaudeCodeProvider(CustomLLM):
    """Improved LiteLLM provider for Claude Code SDK with full parameter support."""
    
    def __init__(self):
        super().__init__()
        if not SDK_AVAILABLE:
            raise ImportError("Claude Code SDK is required. Install with: pip install claude-code-sdk")
        print("ImprovedClaudeCodeProvider initialized")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Claude models."""
        # Claude typically uses ~1.3 tokens per word
        # This is a rough approximation
        words = len(text.split())
        return int(words * 1.3)
    
    def extract_system_prompt(self, messages: List[Dict]) -> Tuple[Optional[str], List[Dict]]:
        """Extract system messages and return (system_prompt, other_messages)."""
        system_prompts = []
        other_messages = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                system_prompts.append(content)
            else:
                other_messages.append(message)
        
        # Combine multiple system messages with newlines
        system_prompt = "\n\n".join(system_prompts) if system_prompts else None
        
        return system_prompt, other_messages
    
    def format_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert LiteLLM messages to Claude prompt format."""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
            # Note: system messages are handled separately via system_prompt
        
        return "\n\n".join(prompt_parts)
    
    def extract_claude_model(self, model: str) -> str:
        """Extract Claude model name from LiteLLM model parameter."""
        # Handle "claude-code-sdk/model-name" -> "model-name"
        # Or just "model-name" -> "model-name"
        return model.split('/')[-1] if '/' in model else model
    
    def build_options(self, model: str, messages: List[Dict], **kwargs) -> Tuple[ClaudeCodeOptions, str]:
        """Build ClaudeCodeOptions with all supported parameters."""
        system_prompt, other_messages = self.extract_system_prompt(messages)
        prompt = self.format_messages_to_prompt(other_messages)
        claude_model = self.extract_claude_model(model)
        
        # Build options with all supported SDK parameters
        options_dict = {
            'model': claude_model
        }
        
        # Add system prompt if present
        if system_prompt:
            options_dict['system_prompt'] = system_prompt
        
        # Add other supported parameters if provided
        supported_params = ['max_turns', 'allowed_tools', 'permission_mode', 'cwd']
        for param in supported_params:
            if param in kwargs and kwargs[param] is not None:
                options_dict[param] = kwargs[param]
        
        # Log ignored parameters for debugging
        ignored_params = ['temperature', 'max_tokens', 'top_p', 'stop_sequences', 'tools', 'tool_choice']
        used_ignored = [p for p in ignored_params if p in kwargs]
        if used_ignored:
            print(f"Warning: Claude Code SDK ignoring parameters: {used_ignored}")
        
        options = ClaudeCodeOptions(**options_dict)
        return options, prompt
    
    def create_litellm_response(self, content: str, model: str, prompt: str) -> ModelResponse:
        """Convert Claude response to LiteLLM format with token estimates."""
        import uuid
        from datetime import datetime
        
        message = LiteLLMMessage(content=content, role="assistant")
        choice = Choices(finish_reason="stop", index=0, message=message)
        
        # Estimate tokens
        prompt_tokens = self.estimate_tokens(prompt)
        completion_tokens = self.estimate_tokens(content)
        
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
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
        """Async completion using Claude Code SDK."""
        try:
            options, prompt = self.build_options(model, messages, **kwargs)
            
            response_content = ""
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_content += block.text
                        elif isinstance(block, (ToolUseBlock, ToolResultBlock)):
                            # Log tool usage for debugging
                            print(f"Note: Tool block received but not supported: {type(block)}")
            
            return self.create_litellm_response(response_content, model, prompt)
            
        except CLINotFoundError:
            raise Exception(
                "Claude Code CLI not installed. "
                "Run: npm install -g @anthropic-ai/claude-code"
            )
        except CLIConnectionError:
            raise Exception(
                "Failed to connect to Claude Code. "
                "Run: claude-code login"
            )
        except ProcessError as e:
            raise Exception(f"Claude Code process failed with exit code {e.exit_code}")
        except CLIJSONDecodeError as e:
            raise Exception(f"Failed to parse Claude Code response: {e}")
        except Exception as e:
            print(f"Claude Code SDK error: {e}")
            raise
    
    def streaming(self, model: str, messages: List[Dict], **kwargs) -> Iterator[GenericStreamingChunk]:
        """Sync streaming - not supported."""
        raise NotImplementedError(
            "Sync streaming is not supported by Claude Code SDK. "
            "Use async streaming with stream=True in an async context."
        )
    
    async def astreaming(self, model: str, messages: List[Dict], **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """Async streaming using Claude Code SDK."""
        try:
            options, prompt = self.build_options(model, messages, **kwargs)
            
            total_content = ""
            chunk_index = 0
            
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            content = block.text
                            total_content += content
                            
                            # Yield content as received, no artificial splitting
                            chunk: GenericStreamingChunk = {
                                "text": content,
                                "is_finished": False,
                                "finish_reason": None,
                                "index": chunk_index,
                                "tool_use": None,
                                "usage": None
                            }
                            chunk_index += 1
                            yield chunk
                        
                        elif isinstance(block, (ToolUseBlock, ToolResultBlock)):
                            # Log for debugging
                            print(f"Note: Tool block in stream but not supported: {type(block)}")
            
            # Send final chunk with token usage estimates
            final_chunk: GenericStreamingChunk = {
                "text": "",
                "is_finished": True,
                "finish_reason": "stop",
                "index": chunk_index,
                "tool_use": None,
                "usage": {
                    "completion_tokens": self.estimate_tokens(total_content),
                    "prompt_tokens": self.estimate_tokens(prompt),
                    "total_tokens": self.estimate_tokens(prompt) + self.estimate_tokens(total_content)
                }
            }
            
            yield final_chunk
            
        except CLINotFoundError:
            raise Exception(
                "Claude Code CLI not installed. "
                "Run: npm install -g @anthropic-ai/claude-code"
            )
        except CLIConnectionError:
            raise Exception(
                "Failed to connect to Claude Code. "
                "Run: claude-code login"
            )
        except ProcessError as e:
            raise Exception(f"Claude Code process failed with exit code {e.exit_code}")
        except CLIJSONDecodeError as e:
            raise Exception(f"Failed to parse Claude Code response: {e}")
        except Exception as e:
            print(f"Claude Code SDK streaming error: {e}")
            raise


# Usage Instructions:
# 1. Replace the current provider with this improved version
# 2. Update YAML config to use the same model mappings
# 3. Document the supported parameters:
#    - model: Claude model selection
#    - System messages: Automatically extracted and passed via system_prompt
#    - max_turns: Limit conversation turns (SDK specific)
#    - allowed_tools: Enable specific tools like Read, Write, Bash
#    - permission_mode: Control edit permissions (e.g., 'acceptEdits')
#    - cwd: Set working directory
#
# 4. Document unsupported parameters:
#    - temperature, top_p, max_tokens, stop_sequences
#    - tools/function calling (OpenAI style)
#    - vision/image input
#    - JSON response format
#    - Accurate token usage (estimates only)