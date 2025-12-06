# Claude Code SDK Tool Analysis

## Summary

Based on analyzing the official `anthropics/claude-code-sdk-python` repository, I found the following evidence about tools in Claude Code:

1. **Tools are passed as string names** to the Claude Code CLI
2. **The SDK handles tools through `allowed_tools` and `disallowed_tools` parameters**
3. **Specific tools found in SDK code: Read, Write, Edit, Bash**
4. **The SDK itself does not contain a complete list of available tools**

## Key Findings

### 1. ClaudeCodeOptions Structure (types.py)

From `src/claude_code_sdk/types.py` (lines 90-102):
```python
@dataclass
class ClaudeCodeOptions:
    """Query options for Claude SDK."""
    
    allowed_tools: list[str] = field(default_factory=list)
    # ... other fields ...
    disallowed_tools: list[str] = field(default_factory=list)
```

**Evidence**: Tools are referenced by string names in lists.

### 2. How Tools Are Passed to CLI (subprocess_cli.py)

From `src/claude_code_sdk/_internal/transport/subprocess_cli.py` (lines 82-87):
```python
if self._options.allowed_tools:
    cmd.extend(["--allowedTools", ",".join(self._options.allowed_tools)])

if self._options.disallowed_tools:
    cmd.extend(["--disallowedTools", ",".join(self._options.disallowed_tools)])
```

**Evidence**: Tools are passed as comma-separated strings to the Claude Code CLI via command-line arguments.

### 3. Specific Tools Found in Examples and Tests

#### From `examples/quick_start.py` (lines 47-50):
```python
options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write"],
    system_prompt="You are a helpful file assistant.",
)
```

#### From `tests/test_types.py` (lines 91-96):
```python
options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write", "Edit"], 
    disallowed_tools=["Bash"]
)
```

#### From `README.md` (lines 55-58):
```python
options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits'  # auto-accept file edits
)
```

### 4. Tools Mentioned in Code

The following tools are explicitly mentioned in the SDK:

| Tool Name | Evidence Location | Context |
|-----------|------------------|---------|
| Read | examples/quick_start.py, tests/test_types.py, tests/test_integration.py, README.md | Reading files |
| Write | examples/quick_start.py, tests/test_types.py, README.md | Writing files |
| Edit | tests/test_types.py | Editing files |
| Bash | tests/test_types.py, README.md | Running bash commands |

### 5. Tool Usage Pattern

From `tests/test_integration.py` (lines 94-102), we can see how tools are used:
```python
{
    "type": "tool_use",
    "id": "tool-123",
    "name": "Read",
    "input": {"file_path": "/test.txt"},
}
```

**Evidence**: Tools are invoked with a name and input parameters.

### 6. External Documentation Reference

The README.md points to external documentation for the complete list of tools:
```markdown
## Available Tools

See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/security#tools-available-to-claude) for a complete list of available tools.
```

## What the SDK Doesn't Reveal

The SDK source code does **NOT** contain:
- A complete list of all available tools
- Tool descriptions or documentation
- Tool parameter schemas
- Tool categories or groupings
- Tools like WebSearch, Grep, LS, Glob, MultiEdit, TodoRead, TodoWrite, etc. (which we know exist)

## Conclusion

The Claude Code SDK Python repository only shows:
1. The mechanism for passing tool names (as strings)
2. A few example tools used in tests/documentation (Read, Write, Edit, Bash)
3. That the complete tool list is maintained elsewhere (likely in the Claude Code CLI itself)

The SDK is designed to be tool-agnostic - it simply passes tool names as strings to the underlying CLI without validating or listing what tools are available. This suggests that the actual tool definitions and available tools are managed by the Claude Code CLI binary, not the Python SDK.

## Next Steps

To find the complete list of available tools, we would need to:
1. Check the Claude Code CLI source code (Node.js)
2. Check the official Anthropic documentation
3. Examine the Claude Code binary itself
4. Look for tool definitions in the Claude backend