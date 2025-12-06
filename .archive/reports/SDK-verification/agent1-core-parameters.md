# Claude Code SDK Core Parameters Investigation Report

## Executive Summary

After a thorough investigation of the Claude Code SDK Python repository (anthropics/claude-code-sdk-python), I can definitively confirm that **NONE** of the following parameters are supported by the Claude Code SDK:

- ❌ **temperature** - NOT supported
- ❌ **max_tokens** - NOT supported
- ❌ **stop_sequences** - NOT supported
- ❌ **top_p** - NOT supported
- ❌ **top_k** - NOT supported

These parameters, which are standard in the Anthropic API, are completely absent from the Claude Code SDK implementation. The SDK uses a fundamentally different approach focused on interactive tool use and code execution rather than traditional LLM parameters.

## Parameter-by-Parameter Analysis

### 1. temperature
**Status:** NOT SUPPORTED

**Evidence:**
- Not present in `ClaudeCodeOptions` dataclass (src/claude_code_sdk/types.py, lines 96-111)
- Not handled in `_build_command` method (src/claude_code_sdk/_internal/transport/subprocess_cli.py, lines 71-113)
- No references found in entire codebase via GitHub search

**What IS there:** The ClaudeCodeOptions class contains these fields instead:
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

### 2. max_tokens
**Status:** NOT SUPPORTED

**Evidence:**
- Not present in ClaudeCodeOptions
- Not handled in command building
- The only "max" parameter is `max_thinking_tokens: int = 8000` (line 98 in types.py)
- No `--max-tokens` flag in CLI command construction

**What's different:** The SDK has `max_thinking_tokens` instead, which appears to control a different aspect of the model's behavior (thinking/reasoning tokens rather than output tokens).

### 3. stop_sequences
**Status:** NOT SUPPORTED

**Evidence:**
- Completely absent from types.py
- Not referenced in subprocess_cli.py command building
- Zero search results for "stop" in the repository

**Command building method shows no stop sequence handling:**
```python
def _build_command(self) -> list[str]:
    """Build CLI command with arguments."""
    cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]
    
    # Only these parameters are supported:
    if self._options.system_prompt:
        cmd.extend(["--system-prompt", self._options.system_prompt])
    # ... (other options, but no stop_sequences)
```

### 4. top_p
**Status:** NOT SUPPORTED

**Evidence:**
- Not in ClaudeCodeOptions dataclass
- Not in command building logic
- Zero search results in repository

### 5. top_k
**Status:** NOT SUPPORTED

**Evidence:**
- Not in ClaudeCodeOptions dataclass
- Not in command building logic  
- Zero search results in repository

## Comparison with Anthropic API

The Anthropic API supports all these parameters as standard options for controlling generation:
- `temperature`: Controls randomness (0-1)
- `max_tokens`: Maximum number of tokens to generate
- `stop_sequences`: Array of sequences that stop generation
- `top_p`: Nucleus sampling threshold
- `top_k`: Top-k sampling parameter

## Why the SDK Doesn't Support These Parameters

The Claude Code SDK appears to be designed for a different use case than the standard Anthropic API:

1. **Interactive Tool Use Focus**: The SDK is optimized for code execution, file manipulation, and tool use rather than text generation control.

2. **CLI Wrapper Architecture**: The SDK wraps the Claude Code CLI tool, which may not expose these low-level generation parameters.

3. **Different Abstraction Level**: The SDK provides high-level features like:
   - Tool permissions (`allowed_tools`, `disallowed_tools`)
   - Session management (`continue_conversation`, `resume`)
   - Working directory control (`cwd`)
   - MCP server integration

4. **Opinionated Defaults**: The CLI likely uses pre-configured generation settings optimized for code tasks.

## File Paths and Line Numbers

- **ClaudeCodeOptions definition**: `src/claude_code_sdk/types.py`, lines 96-111
- **Command building logic**: `src/claude_code_sdk/_internal/transport/subprocess_cli.py`, lines 71-113
- **Client implementation**: `src/claude_code_sdk/_internal/client.py`, entire file
- **Public API**: `src/claude_code_sdk/__init__.py`, lines 55-94

## Definitive Conclusions

1. The Claude Code SDK does NOT support traditional LLM generation parameters (temperature, max_tokens, stop_sequences, top_p, top_k).

2. The SDK is designed for a specific use case (interactive code assistance) and abstracts away low-level generation control.

3. If these parameters are required, users must use the standard Anthropic API directly rather than the Claude Code SDK.

4. The only "thinking" related parameter is `max_thinking_tokens`, which serves a different purpose than `max_tokens`.

5. Any attempt to pass these parameters to the SDK will be silently ignored as they are not part of the `ClaudeCodeOptions` interface.

## Verification

A verification script has been created at `agent-results/verify_parameters.py` that demonstrates:
- The actual fields available in `ClaudeCodeOptions`
- The absence of standard LLM parameters
- What happens when you try to use unsupported parameters (TypeError)

## Implications for LiteLLM Integration

For the LiteLLM Claude Code Provider project:
1. These parameters cannot be passed through to the Claude Code SDK
2. Any requests with these parameters must either:
   - Ignore them (current behavior)
   - Return an error/warning to the user
   - Document this limitation clearly
3. The provider can only support parameters that exist in `ClaudeCodeOptions`