# Claude Code SDK Feature Verification Report

## Executive Summary

**All five claimed SDK-specific features are CONFIRMED and FULLY SUPPORTED** in the Claude Code SDK Python implementation:

1. ✅ **allowed_tools** - Supported
2. ✅ **permission_mode** - Supported
3. ✅ **cwd** - Supported
4. ✅ **max_turns** - Supported
5. ✅ **system_prompt** - Supported

Each feature has been verified through direct source code examination from the official anthropics/claude-code-sdk-python repository.

## Feature-by-Feature Analysis

### 1. allowed_tools

**Definition in types.py (line 103):**
```python
@dataclass
class ClaudeCodeOptions:
    """Query options for Claude SDK."""
    
    allowed_tools: list[str] = field(default_factory=list)
```

**CLI Implementation in subprocess_cli.py (lines 81-82):**
```python
if self._options.allowed_tools:
    cmd.extend(["--allowedTools", ",".join(self._options.allowed_tools)])
```

**Type:** `list[str]`  
**Default:** Empty list  
**CLI Flag:** `--allowedTools`  
**Format:** Comma-separated string when passed to CLI

**Usage Example:**
```python
options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write", "Bash"]
)
```

### 2. permission_mode

**Definition in types.py (lines 9, 109):**
```python
# Permission modes
PermissionMode = Literal["default", "acceptEdits", "bypassPermissions"]

@dataclass
class ClaudeCodeOptions:
    permission_mode: PermissionMode | None = None
```

**CLI Implementation in subprocess_cli.py (lines 99-100):**
```python
if self._options.permission_mode:
    cmd.extend(["--permission-mode", self._options.permission_mode])
```

**Type:** `Literal["default", "acceptEdits", "bypassPermissions"] | None`  
**Default:** `None`  
**CLI Flag:** `--permission-mode`  
**Valid Values:** "default", "acceptEdits", "bypassPermissions"

**Usage Example:**
```python
options = ClaudeCodeOptions(
    permission_mode="acceptEdits"  # Auto-accept file edits
)
```

### 3. cwd (Current Working Directory)

**Definition in types.py (line 115):**
```python
@dataclass
class ClaudeCodeOptions:
    cwd: str | Path | None = None
```

**CLI Implementation in subprocess_cli.py (lines 31, 123):**
```python
def __init__(self, prompt: str, options: ClaudeCodeOptions, cli_path: str | Path | None = None):
    self._cwd = str(options.cwd) if options.cwd else None

# Later in connect()
self._process = await anyio.open_process(
    cmd,
    stdin=None,
    stdout=PIPE,
    stderr=PIPE,
    cwd=self._cwd,  # Passed directly to subprocess
    env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": "sdk-py"},
)
```

**Type:** `str | Path | None`  
**Default:** `None` (uses current directory)  
**Implementation:** Passed directly to subprocess as working directory

**Usage Example:**
```python
from pathlib import Path

options = ClaudeCodeOptions(
    cwd="/path/to/project"  # or Path("/path/to/project")
)
```

### 4. max_turns

**Definition in types.py (line 111):**
```python
@dataclass
class ClaudeCodeOptions:
    max_turns: int | None = None
```

**CLI Implementation in subprocess_cli.py (lines 84-85):**
```python
if self._options.max_turns:
    cmd.extend(["--max-turns", str(self._options.max_turns)])
```

**Type:** `int | None`  
**Default:** `None` (no limit)  
**CLI Flag:** `--max-turns`  
**Format:** Converted to string for CLI

**Usage Example:**
```python
options = ClaudeCodeOptions(
    max_turns=5  # Limit conversation to 5 turns
)
```

### 5. system_prompt

**Definition in types.py (line 105):**
```python
@dataclass
class ClaudeCodeOptions:
    system_prompt: str | None = None
```

**CLI Implementation in subprocess_cli.py (lines 75-76):**
```python
if self._options.system_prompt:
    cmd.extend(["--system-prompt", self._options.system_prompt])
```

**Type:** `str | None`  
**Default:** `None`  
**CLI Flag:** `--system-prompt`  
**Note:** This is separate from the messages array and provides a persistent system instruction

**Usage Example:**
```python
options = ClaudeCodeOptions(
    system_prompt="You are a helpful assistant"
)
```

## Additional SDK Features Found

During investigation, several other SDK-specific features were discovered:

1. **append_system_prompt** (line 106) - Appends to existing system prompt
2. **mcp_tools** (line 107) - MCP tool configuration
3. **mcp_servers** (line 108) - MCP server configuration
4. **continue_conversation** (line 110) - Continue previous conversation
5. **resume** (line 111) - Resume specific session ID
6. **disallowed_tools** (line 112) - Explicitly disallow certain tools
7. **model** (line 113) - Specify which Claude model to use
8. **permission_prompt_tool_name** (line 114) - Custom permission prompt tool

## Command Building Logic

The `_build_command()` method in subprocess_cli.py (lines 71-113) demonstrates how all options are converted to CLI arguments:

```python
def _build_command(self) -> list[str]:
    """Build CLI command with arguments."""
    cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]
    
    # All SDK options are conditionally added as CLI flags
    if self._options.system_prompt:
        cmd.extend(["--system-prompt", self._options.system_prompt])
    # ... (other options follow same pattern)
    
    cmd.extend(["--print", self._prompt])
    return cmd
```

## Test Coverage

The test file `test_transport.py` demonstrates real usage:

```python
def test_build_command_with_options(self):
    transport = SubprocessCLITransport(
        prompt="test",
        options=ClaudeCodeOptions(
            system_prompt="Be helpful",
            allowed_tools=["Read", "Write"],
            disallowed_tools=["Bash"],
            model="claude-3-5-sonnet",
            permission_mode="acceptEdits",
            max_turns=5,
        ),
        cli_path="/usr/bin/claude",
    )
```

## Conclusion

All five SDK-specific features are fully implemented and functional in the Claude Code SDK. The implementation follows a consistent pattern:

1. Options are defined as dataclass fields in `ClaudeCodeOptions`
2. Each option has appropriate type hints and defaults
3. Options are converted to CLI arguments in `_build_command()`
4. The subprocess is spawned with these arguments

The SDK provides comprehensive control over Claude's behavior, tool usage, permissions, and execution environment, making it suitable for integration into larger applications requiring programmatic AI assistance.