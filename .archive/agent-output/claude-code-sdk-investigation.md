# Claude Code SDK Investigation Report

## Executive Summary

The Claude Code SDK provides a limited subset of features compared to the official Anthropic API. It's designed specifically for code-related tasks and uses OAuth authentication instead of API keys. After examining the SDK source code, we've confirmed that the SDK has hardcoded limitations that cannot be overcome, particularly around streaming behavior.

## Feature Compatibility Matrix

| Feature | Anthropic API | Claude Code SDK | Our Implementation | Can Implement? |
|---------|---------------|-----------------|-------------------|----------------|
| **Basic Parameters** |
| temperature | ✅ | ❌ | ❌ | ❌ |
| max_tokens | ✅ | ❌ | ❌ | ❌ |
| stop_sequences | ✅ | ❌ | ❌ | ❌ |
| top_p | ✅ | ❌ | ❌ | ❌ |
| top_k | ✅ | ❌ | ❌ | ❌ |
| **Model Selection** |
| Model specification | ✅ | ✅ | ✅ | ✅ |
| **Message Handling** |
| System messages | ✅ | ✅ (via system_prompt) | ❌ | ✅ |
| User messages | ✅ | ✅ | ✅ | ✅ |
| Assistant messages | ✅ | ✅ | ✅ | ✅ |
| **Streaming** |
| Basic streaming | ✅ | ✅ | ✅ (chunky) | ✅ |
| Smooth streaming | ✅ | ❌ (large chunks) | ❌ | ⚠️ |
| **Advanced Features** |
| Tool/function calling | ✅ | ❌ | ❌ | ❌ |
| Vision/image input | ✅ | ❌ | ❌ | ❌ |
| Web search | ✅ | ❌ | ❌ | ❌ |
| Token usage reporting | ✅ | ✅ (actual) | ❌ (fake) | ✅ |
| Response format (JSON) | ✅ | ❌ | ❌ | ❌ |
| **SDK-Specific Features** |
| allowed_tools | N/A | ✅ | ❌ | ✅ |
| permission_mode | N/A | ✅ | ❌ | ✅ |
| cwd | N/A | ✅ | ❌ | ✅ |
| max_turns | N/A | ✅ | ❌ | ✅ |
| **Authentication** |
| API Key | ✅ | ❌ | N/A | N/A |
| OAuth | ❌ | ✅ | ✅ | ✅ |

## Key Findings

### 1. Claude Code SDK Limitations (Source Code Confirmed)

The Claude Code SDK is **NOT** a general-purpose wrapper for the Anthropic API. After examining the source code, we can definitively state:

**Hardcoded Limitations:**
- **Output format locked**: `subprocess_cli.py:73` hardcodes `--output-format stream-json`
- **No temperature control**: Not in `ClaudeCodeOptions` type definition
- **No token limits**: Cannot set max_tokens
- **No stop sequences**: Cannot define custom stopping points
- **No advanced sampling**: No top_p, top_k parameters
- **No tool/function calling**: Cannot use OpenAI-style function calling
- **No vision support**: Cannot process images
- **Token usage data**: SDK returns actual API token counts in `ResultMessage` (not estimates)

### 2. What the SDK DOES Support

- **Model selection**: Can specify which Claude model to use
- **System prompts**: Via `system_prompt` option
- **Code-specific tools**: Read, Write, Bash, etc. (for file operations)
- **Working directory**: Can set current working directory
- **Turn limits**: Can limit conversation turns
- **Permission modes**: Control over file edit permissions
- **Additional features**: append_system_prompt, disallowed_tools, mcp_servers, continue_conversation, resume, max_thinking_tokens

### 3. Streaming Architecture (Definitively Confirmed)

Based on source code analysis:

1. **Hardcoded message-level streaming**: 
   - `subprocess_cli.py:73`: Always uses `--output-format stream-json`
   - `subprocess_cli.py:175-185`: Parses complete JSON messages line by line
   - `client.py:44-71`: Each message contains complete `TextBlock` with full text

2. **No alternative transport**:
   - Only `SubprocessCLITransport` exists
   - No configuration to change output format
   - No mechanism for character-level updates

3. **JSON structure**: Each line is a complete message:
   ```json
   {"type": "assistant", "message": {"content": [{"type": "text", "text": "Complete response text"}]}}
   ```

### 4. Authentication Differences

- **Anthropic API**: Uses API keys (`ANTHROPIC_API_KEY`)
- **Claude Code SDK**: Uses OAuth via `claude-code login`
- This is a fundamental architectural difference

## Immediate Recommendations

### 1. Parameters to Add NOW

These SDK-supported parameters should be added to our provider immediately:

```python
options = ClaudeCodeOptions(
    model=claude_model,
    system_prompt=system_message,  # Extract from messages
    max_turns=kwargs.get('max_turns', None),
    allowed_tools=kwargs.get('allowed_tools', None),
    permission_mode=kwargs.get('permission_mode', None),
    cwd=kwargs.get('cwd', None),
    append_system_prompt=kwargs.get('append_system_prompt', None),
    disallowed_tools=kwargs.get('disallowed_tools', None),
    mcp_servers=kwargs.get('mcp_servers', None),
    mcp_tools=kwargs.get('mcp_tools', None),
    continue_conversation=kwargs.get('continue_conversation', False),
    resume=kwargs.get('resume', None),
    max_thinking_tokens=kwargs.get('max_thinking_tokens', 8000)
)
```

### 2. Improve Message Handling

Instead of converting system messages to prompts, use the dedicated `system_prompt` parameter:

```python
def extract_system_prompt(self, messages: List[Dict]) -> tuple[str, List[Dict]]:
    """Extract system message and return (system_prompt, remaining_messages)."""
    system_prompt = None
    other_messages = []
    
    for message in messages:
        if message.get('role') == 'system':
            system_prompt = message.get('content', '')
        else:
            other_messages.append(message)
    
    return system_prompt, other_messages
```

### 3. Document Unsupported Features

Create clear documentation stating that these features are NOT supported:
- Temperature, top_p, max_tokens, stop_sequences
- Tool/function calling (OpenAI-style)
- Vision/image processing
- Web search
- JSON response format

Note: Token usage IS accurately reported by the SDK in ResultMessage

### 4. Streaming Improvements

While we can't fix the fundamental chunking issue, we can:
- Remove the manual text splitting (it doesn't help)
- Consider buffering strategies for smoother output
- Set realistic expectations about streaming quality

## Testing Requirements

To verify these findings, we need tests for:

1. **Parameter handling**: Verify which parameters are silently ignored vs cause errors
2. **System prompt**: Test if system_prompt option works correctly
3. **Model selection**: Verify all Claude models work
4. **Streaming behavior**: Measure actual chunk sizes and timing
5. **Error handling**: Test behavior with unsupported parameters

## Conclusion

The Claude Code SDK is a specialized tool for code-related tasks, not a general-purpose LLM interface. While we can improve our implementation by adding support for SDK-specific parameters, we cannot achieve feature parity with the Anthropic API. Users expecting full API compatibility will be disappointed.

### Key Updates from Verification:
1. **Token usage is real**: The SDK returns actual API token counts, not estimates
2. **More features available**: Additional parameters like mcp_servers, continue_conversation, etc.
3. **All claims verified**: Source code analysis confirms the architectural limitations

The key value proposition is OAuth authentication instead of API keys, making it suitable for environments where API key management is problematic. However, this comes at the cost of significantly reduced functionality compared to the direct API.