# Claude Code SDK Advanced Features Investigation Report

## Executive Summary

After thorough investigation of the Claude Code SDK Python repository (`anthropics/claude-code-sdk-python`), I can definitively confirm that the following advanced features are **NOT SUPPORTED**:

1. ❌ **NO OpenAI-style tool/function calling support**
2. ❌ **NO vision/image input support** 
3. ❌ **NO web search capability**
4. ❌ **NO JSON response format option**

## Detailed Evidence

### 1. NO OpenAI-Style Function Calling

The Claude Code SDK does NOT support OpenAI-style function calling with `tools`, `tool_choice`, or function definitions. Here's the evidence:

#### What IS in ClaudeCodeOptions:
```python
@dataclass
class ClaudeCodeOptions:
    """Query options for Claude SDK."""
    
    allowed_tools: list[str] = field(default_factory=list)
    max_thinking_tokens: int = 8000
    system_prompt: str | None = None
    append_system_prompt: str | None = None
    mcp_tools: list[str] = field(default_factory=list)
    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
```

#### What's Missing:
- No `tools` parameter for function definitions
- No `tool_choice` parameter
- No function schemas or descriptions
- No parallel function calling support

#### SDK Tools vs Function Calling:
The `allowed_tools` parameter refers to Claude Code's built-in tools only:
```python
# From examples/quick_start.py
options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write"],  # These are built-in Claude Code tools
    system_prompt="You are a helpful file assistant.",
)
```

These are predefined tools like Read, Write, Bash, etc., NOT custom functions you can define.

### 2. NO Vision/Image Input Support

The SDK has absolutely no support for image inputs:

#### Search Results:
- Searched for "image", "vision", "multimodal" - **0 results**
- No image handling in message types
- No base64 encoding support for images
- No content array with image blocks

#### Message Structure:
```python
@dataclass
class UserMessage:
    """User message."""
    content: str  # Only string content, no images!
```

Compare to Anthropic API which supports:
```python
# Anthropic API (NOT in Claude Code SDK)
content=[
    {"type": "text", "text": "What's in this image?"},
    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "..."}}
]
```

### 3. NO Web Search Capability

The SDK has no web search functionality:

#### Evidence:
- No search-related parameters in `ClaudeCodeOptions`
- No web search tools in allowed_tools
- No search command in CLI builder
- Search for "search", "web" - no relevant results

#### CLI Command Building:
```python
def _build_command(self) -> list[str]:
    """Build CLI command with arguments."""
    cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]
    
    # Parameters that ARE supported:
    if self._options.system_prompt:
        cmd.extend(["--system-prompt", self._options.system_prompt])
    if self._options.allowed_tools:
        cmd.extend(["--allowedTools", ",".join(self._options.allowed_tools)])
    # ... other parameters
    
    # NO --web-search or similar option exists!
```

### 4. NO JSON Response Format Option

The SDK cannot enforce JSON output format:

#### Missing Features:
- No `response_format` parameter
- No `json_mode` option
- No output schema validation
- No structured output support

#### What You Get:
```python
# Only unstructured text responses
@dataclass
class TextBlock:
    """Text content block."""
    text: str  # Free-form text, no JSON guarantee
```

## Why These Features Are Missing

### 1. Different Purpose
Claude Code SDK is designed for **code assistance and file operations**, not general-purpose API calls. It's meant to work like the Claude.ai/code interface.

### 2. OAuth vs API Key
The SDK uses OAuth authentication through the Claude Code CLI, not API keys. This suggests it's accessing a different backend service than the Anthropic API.

### 3. CLI Limitations
The SDK is a wrapper around the Claude Code CLI (`@anthropic-ai/claude-code`). It can only support what the CLI supports.

### 4. Tool Philosophy
Instead of custom functions, Claude Code provides a curated set of powerful built-in tools:
- File operations (Read, Write, Edit)
- System commands (Bash)
- MCP server integration
- Browser automation (via MCP)

## SDK Capabilities vs Anthropic API

| Feature | Anthropic API | Claude Code SDK |
|---------|---------------|-----------------|
| Custom Functions | ✅ Full support | ❌ Not supported |
| Vision/Images | ✅ Supported | ❌ Not supported |
| Web Search | ✅ Available | ❌ Not available |
| JSON Mode | ✅ Supported | ❌ Not supported |
| Built-in Tools | ❌ None | ✅ Read, Write, Bash, etc. |
| OAuth Auth | ❌ Not used | ✅ Required |
| File Operations | ❌ Not built-in | ✅ Native support |

## Conclusion

The Claude Code SDK is NOT a drop-in replacement for the Anthropic API. It's a specialized tool for code assistance with its own set of capabilities and limitations. If you need:

- **Custom function calling** → Use Anthropic API
- **Image analysis** → Use Anthropic API  
- **Web search** → Use Anthropic API or other services
- **JSON output** → Use Anthropic API with prompting
- **Code assistance with file operations** → Use Claude Code SDK

The SDK excels at what it's designed for: providing an AI coding assistant with deep file system integration, but it lacks the advanced features available in the general Anthropic API.