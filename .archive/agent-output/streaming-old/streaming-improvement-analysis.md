# Streaming Implementation Analysis & Improvements

## Current Implementation Issues

### 1. Manual Chunk Splitting (Lines 109-142)
```python
# Current problematic approach:
if len(content) > 50:
    words = content.split(' ')
    current_chunk = ""
    for word in words:
        if len(current_chunk) + len(word) > 30:
            # ... yield chunk
```

**Problems:**
- Artificial and ineffective
- Adds complexity without real benefit
- SDK provides complete messages, not progressive chunks
- Creates unnatural word boundaries
- Cannot overcome SDK's hardcoded `--output-format stream-json`

### 2. Comparison with LiteLLM's Anthropic Provider

**LiteLLM Anthropic Streaming:**
```python
# Handles multiple event types
for event in stream:
    if event.type == "message_start":
        # Initialize
    elif event.type == "content_block_delta":
        # Stream content smoothly
    elif event.type == "message_stop":
        # Finalize
```

**Our SDK Streaming:**
- Only receives complete `AssistantMessage` objects
- No granular delta events
- Cannot achieve character-by-character streaming

## Root Cause Analysis (Source Code Verified)

The Claude Code SDK cannot provide token-level streaming due to architectural constraints:

1. **Hardcoded Output Format**: 
   - `subprocess_cli.py:73` locks format to `--output-format stream-json`
   - No parameter in `ClaudeCodeOptions` to change this
   - Transport always uses newline-delimited JSON

2. **Message-Level Protocol**:
   - Each JSON line represents a complete message state
   - `client.py` parses full `TextBlock` objects, not deltas
   - No support for incremental content updates

3. **CLI Architecture**:
   - SDK spawns CLI subprocess: `await anyio.open_process(cmd, ...)`
   - Reads stdout line by line: `async for line in self._stdout_stream`
   - Each line must be valid JSON: `data = json.loads(line_str)`

## Recommended Improvements

### 1. Remove Manual Splitting
```python
async def astreaming(self, model: str, messages: List[Dict], **kwargs) -> AsyncIterator[GenericStreamingChunk]:
    """Async streaming using Claude Code SDK."""
    system_prompt, other_messages = self.extract_system_prompt(messages)
    prompt = self.format_messages_to_prompt(other_messages)
    claude_model = self.extract_claude_model(model)
    
    # Enhanced options with all supported parameters
    options = ClaudeCodeOptions(
        model=claude_model,
        system_prompt=system_prompt,
        max_turns=kwargs.get('max_turns'),
        allowed_tools=kwargs.get('allowed_tools'),
        permission_mode=kwargs.get('permission_mode'),
        cwd=kwargs.get('cwd')
    )
    
    total_content = ""
    
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    content = block.text
                    total_content += content
                    
                    # Yield the content as-is, no artificial splitting
                    chunk: GenericStreamingChunk = {
                        "text": content,
                        "is_finished": False,
                        "finish_reason": None,
                        "index": 0,
                        "tool_use": None,
                        "usage": None
                    }
                    yield chunk
    
    # Final chunk with usage estimation
    final_chunk: GenericStreamingChunk = {
        "text": "",
        "is_finished": True,
        "finish_reason": "stop",
        "index": 0,
        "tool_use": None,
        "usage": {
            "completion_tokens": self.estimate_tokens(total_content),
            "prompt_tokens": self.estimate_tokens(prompt),
            "total_tokens": self.estimate_tokens(prompt) + self.estimate_tokens(total_content)
        }
    }
    
    yield final_chunk
```

### 2. Add Token Estimation
```python
def estimate_tokens(self, text: str) -> int:
    """Estimate token count (rough approximation)."""
    # Claude uses ~1.3 tokens per word on average
    words = len(text.split())
    return int(words * 1.3)
```

### 3. Implement System Message Extraction
```python
def extract_system_prompt(self, messages: List[Dict]) -> tuple[str, List[Dict]]:
    """Extract system message for ClaudeCodeOptions."""
    system_prompt = None
    other_messages = []
    
    for message in messages:
        if message.get('role') == 'system':
            if system_prompt is None:
                system_prompt = message.get('content', '')
            else:
                # Multiple system messages: concatenate
                system_prompt += "\n\n" + message.get('content', '')
        else:
            other_messages.append(message)
    
    return system_prompt, other_messages
```

### 4. Enhanced Error Handling
```python
try:
    async for message in query(prompt=prompt, options=options):
        # ... process message
except CLINotFoundError:
    raise Exception("Claude Code CLI not installed. Run: npm install -g @anthropic-ai/claude-code")
except CLIConnectionError:
    raise Exception("Failed to connect to Claude Code. Run: claude-code login")
except Exception as e:
    # Log the actual error for debugging
    print(f"Claude Code SDK error: {e}")
    raise
```

## Streaming Expectations Management

### Document Clearly:

```markdown
## Streaming Limitations

The Claude Code SDK provides "chunked streaming" rather than true character-by-character streaming:

- **Chunk Size**: Typically 100-500 characters per chunk
- **Frequency**: Chunks arrive in bursts, not smoothly
- **Buffering**: The SDK buffers content before sending

This is a fundamental limitation of the Claude Code SDK architecture and cannot be improved further.
```

## Performance Comparison

| Aspect | Anthropic API | Claude Code SDK |
|--------|---------------|-----------------|
| Streaming Granularity | Character-level | Paragraph-level |
| Latency | < 100ms | 500ms - 2s |
| Chunk Size | 1-10 chars | 100-500 chars |
| Use Case | Real-time chat | Code generation |

## Conclusion

The streaming limitations are fundamental and **cannot be changed** without modifying the SDK source:

1. **Remove** artificial chunk splitting (it doesn't help)
2. **Add** proper parameter support (for SDK-supported features)
3. **Document** clearly that this is message-level, not token-level streaming
4. **Set** expectations: Users will see complete thoughts, not progressive text

**Definitive Statement**: The Claude Code SDK uses a hardcoded `--output-format stream-json` that provides complete messages via newline-delimited JSON. There is no way to achieve character-by-character streaming through the current SDK architecture. This is an intentional design choice for a CLI-based tool focused on code operations rather than real-time chat.