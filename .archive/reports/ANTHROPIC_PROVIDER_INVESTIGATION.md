# Investigation Report: LiteLLM Anthropic Provider vs Claude Code SDK Provider

## 1. Missing Parameters

Our current implementation is missing several important parameters that the official Anthropic provider supports:

### Core Parameters
- **`temperature`** - Controls randomness (0-1)
- **`top_p`** - Nucleus sampling parameter
- **`top_k`** - Top-k sampling parameter  
- **`stop`/`stop_sequences`** - Stop sequences for generation
- **`max_tokens`/`max_completion_tokens`** - Maximum tokens to generate
- **`system`** - System messages support
- **`metadata`** - User tracking and custom metadata
- **`response_format`** - JSON mode support
- **`tools`/`tool_choice`** - Function/tool calling support
- **`parallel_tool_calls`** - Parallel tool execution control
- **`stream_options`** - Streaming configuration (e.g., include_usage)
- **`extra_headers`** - Custom HTTP headers
- **`timeout`** - Request timeout control
- **`user`** - User ID for tracking

### Advanced Anthropic Features
- **`thinking`/`reasoning_effort`** - Claude's reasoning/thinking tokens
- **`web_search_options`** - Web search integration
- **`cache_control`** - Prompt caching support
- **MCP servers** - Model Context Protocol support
- **Container upload** - Code execution environments
- **Citations** - Source attribution support

## 2. Implementation Patterns We Should Adopt

### A. Proper Message Formatting
```python
# Current (basic)
def format_messages_to_prompt(self, messages: List[Dict]) -> str:
    prompt_parts = []
    for message in messages:
        # Simple string concatenation
    return "\n\n".join(prompt_parts)

# Better (Anthropic style)
def transform_request(self, model, messages, optional_params, litellm_params, headers):
    # 1. Extract and transform system messages separately
    anthropic_system_message_list = self.translate_system_message(messages)
    
    # 2. Use proper Anthropic message formatting
    anthropic_messages = anthropic_messages_pt(
        model=model,
        messages=messages, 
        llm_provider="anthropic"
    )
    
    # 3. Build proper request structure
    data = {
        "model": model,
        "messages": anthropic_messages,
        "system": anthropic_system_message_list,
        **optional_params
    }
```

### B. Streaming Response Handling
```python
# Current (basic chunking)
async def astreaming(self, model: str, messages: List[Dict], **kwargs):
    # Manual text splitting
    if len(content) > 50:
        words = content.split(' ')
        # Manual chunking logic

# Better (proper streaming chunks)
class ModelResponseIterator:
    def chunk_parser(self, chunk: dict) -> ModelResponseStream:
        # Handle different chunk types properly
        if type_chunk == "content_block_delta":
            # Process text, tool calls, thinking blocks
        elif type_chunk == "content_block_start":
            # Handle block initialization
        elif type_chunk == "message_delta":
            # Process usage, finish reasons
            
        # Return properly formatted streaming chunk
        return ModelResponseStream(
            choices=[StreamingChoices(...)],
            usage=usage,
        )
```

### C. Error Handling
```python
# Current (none)
# No error handling

# Better
class AnthropicError(BaseLLMException):
    def __init__(self, status_code: int, message: str, headers: Optional[httpx.Headers] = None):
        self.status_code = status_code
        self.message = message
        self.headers = headers
        super().__init__(message)
```

### D. Usage Tracking
```python
# Current (hardcoded)
usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)

# Better (calculated)
def calculate_usage(self, usage_object: dict, reasoning_content: Optional[str]) -> Usage:
    prompt_tokens = usage_object.get("input_tokens", 0)
    completion_tokens = usage_object.get("output_tokens", 0)
    
    # Handle cache tokens
    cache_creation_input_tokens = usage_object.get("cache_creation_input_tokens", 0)
    cache_read_input_tokens = usage_object.get("cache_read_input_tokens", 0)
    
    # Handle reasoning tokens
    completion_token_details = CompletionTokensDetailsWrapper(
        reasoning_tokens=token_counter(text=reasoning_content, count_response_tokens=True)
    ) if reasoning_content else None
    
    return Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        prompt_tokens_details=prompt_tokens_details,
        completion_tokens_details=completion_token_details,
        cache_creation_input_tokens=cache_creation_input_tokens,
        cache_read_input_tokens=cache_read_input_tokens,
    )
```

## 3. Specific Recommendations

### A. Inherit from BaseConfig
```python
from litellm.llms.base_llm.chat.transformation import BaseConfig

class ClaudeCodeConfig(BaseConfig):
    @property
    def custom_llm_provider(self) -> str:
        return "claude-code-sdk"
    
    def get_supported_openai_params(self, model: str):
        return [
            "stream", "stop", "temperature", "top_p", "max_tokens",
            "tools", "tool_choice", "extra_headers", "timeout",
            "response_format", "user", "metadata"
        ]
    
    def map_openai_params(self, non_default_params, optional_params, model, drop_params):
        # Map OpenAI params to Claude SDK format
        for param, value in non_default_params.items():
            if param == "temperature":
                optional_params["temperature"] = value
            # ... etc
        return optional_params
```

### B. Implement Proper Response Transformation
```python
def transform_response(self, model, raw_response, model_response, logging_obj, **kwargs):
    # Extract content, tool calls, usage
    text_content, tool_calls, usage = self.extract_response_content(raw_response)
    
    # Build proper message object
    message = litellm.Message(
        content=text_content,
        tool_calls=tool_calls,
        role="assistant"
    )
    
    # Set on model response
    model_response.choices[0].message = message
    model_response.usage = usage
    
    return model_response
```

### C. Add Parameter Support in ClaudeCodeOptions
```python
# When creating options
options = ClaudeCodeOptions(
    model=claude_model,
    temperature=kwargs.get("temperature"),
    max_tokens=kwargs.get("max_tokens"),
    stop_sequences=kwargs.get("stop"),
    # ... other params if Claude SDK supports them
)
```

### D. Implement Async HTTP Client Usage
```python
from litellm.llms.custom_httpx.http_handler import AsyncHTTPHandler, get_async_httpx_client

async def acompletion(self, model, messages, client=None, **kwargs):
    if client is None:
        client = get_async_httpx_client(llm_provider=litellm.LlmProviders.CLAUDE_CODE_SDK)
    
    # Use client for HTTP operations if needed
```

## 4. Limitations & Considerations

1. **Claude Code SDK Limitations**: Many advanced features (tools, web search, MCP) may not be supported by the Claude Code SDK itself. We should check what the SDK actually supports.

2. **OAuth vs API Key**: The official provider uses API keys while we use OAuth. This is a fundamental difference we need to maintain.

3. **Streaming Format**: The Claude Code SDK may have different streaming formats than the official Anthropic API, requiring custom adaptation.

4. **Model Naming**: We need to maintain our model extraction logic since we're routing through the SDK rather than directly to Anthropic.

## 5. Priority Implementation Order

### High Priority (Basic functionality):
- Add `temperature`, `top_p`, `max_tokens` support
- Implement proper error handling with `ClaudeCodeError`
- Fix usage calculation to use actual token counts
- Add `stop_sequences` support

### Medium Priority (Common features):
- Support system messages properly
- Add `metadata` and `user` tracking
- Implement `timeout` handling
- Add `extra_headers` support

### Low Priority (Advanced features):
- Tool calling support (if SDK supports it)
- Response format / JSON mode
- Caching support
- Web search integration

This investigation shows that our current provider is quite basic compared to the official implementation. The main improvements would come from proper parameter handling, better error management, accurate usage tracking, and more sophisticated message formatting.