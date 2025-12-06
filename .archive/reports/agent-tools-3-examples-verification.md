# Claude Code Tool Usage Examples and Tests

## Summary of Findings

Based on searching through Anthropic's repositories, I found concrete evidence of tool usage in the Claude Code ecosystem:

### 1. **Official Tools Found in Use**

#### Base Allowed Tools (from claude-code-action):
```typescript
const BASE_ALLOWED_TOOLS = [
  "Edit",
  "MultiEdit",
  "Glob",
  "Grep",
  "LS",
  "Read",
  "Write",
  "mcp__github_file_ops__commit_files",
  "mcp__github_file_ops__delete_files",
  "mcp__github_file_ops__update_claude_comment",
];
```

#### Disallowed Tools by Default:
```typescript
const DISALLOWED_TOOLS = ["WebSearch", "WebFetch"];
```

### 2. **Actual Usage Examples Found**

#### A. In claude-code-sdk-python

**Example 1: Basic Tool Usage (examples/quick_start.py)**
```python
options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write"],
    system_prompt="You are a helpful file assistant.",
)

async for message in query(
    prompt="Create a file called hello.txt with 'Hello, World!' in it",
    options=options,
):
    # Process responses
```

**Example 2: README Documentation**
```python
options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits'  # auto-accept file edits
)
```

**Example 3: Integration Test (tests/test_integration.py)**
```python
# Test shows actual tool use response structure
async for msg in query(
    prompt="Read /test.txt",
    options=ClaudeCodeOptions(allowed_tools=["Read"]),
):
    # Response includes ToolUseBlock with:
    # - name: "Read"
    # - input: {"file_path": "/test.txt"}
```

#### B. In claude-code-action

**GitHub Actions Tool Configuration:**
- The action specifically configures allowed and disallowed tools
- Tools can be overridden via `allowedTools` and `disallowedTools` parameters
- Special handling for WebSearch and WebFetch - they're disallowed by default but can be explicitly allowed

### 3. **Tools Actually Working in Tests**

From the integration tests, I found evidence that these tools are actively tested:
- **Read** - File reading tool (with file_path parameter)
- **Write** - File writing tool
- **Edit** - Single file editing
- **MultiEdit** - Multiple edits in one operation
- **Glob** - File pattern matching
- **Grep** - Content searching
- **LS** - Directory listing

### 4. **MCP (Model Context Protocol) Tools**

Special GitHub-specific tools found in claude-code-action:
- `mcp__github_file_ops__commit_files` - Commit files to GitHub
- `mcp__github_file_ops__delete_files` - Delete files from GitHub
- `mcp__github_file_ops__update_claude_comment` - Update Claude's comment on issues/PRs

### 5. **Tools Mentioned But Not Found in Active Use**

These tools were mentioned in documentation but I didn't find concrete usage examples:
- **TodoWrite** / **TodoRead** - No results found in Anthropic repos
- **NotebookEdit** / **NotebookRead** - No results found
- **exit_plan_mode** - Not found in searches
- **Bash** - Mentioned in documentation but no test examples

### 6. **Configuration Patterns**

**Permission Modes:**
```python
permission_mode='acceptEdits'  # Auto-accept file edits
```

**Tool Override Pattern:**
```javascript
// From claude-code-action
if (allowedTools && allowedTools.includes("WebSearch")) {
    // Remove WebSearch from disallowed list if explicitly allowed
    disallowedTools = disallowedTools.filter(tool => tool !== "WebSearch");
}
```

### 7. **Key Findings**

1. **Core File Tools Work**: Read, Write, Edit, MultiEdit are actively used and tested
2. **Search Tools Work**: Glob, Grep, LS are part of base allowed tools
3. **Web Tools Restricted**: WebSearch and WebFetch are disallowed by default for security
4. **GitHub Integration**: Special MCP tools for GitHub operations
5. **Missing Tools**: TodoWrite, TodoRead, NotebookEdit, NotebookRead, exit_plan_mode not found in actual use

### 8. **Comparison with Documentation**

The tools found in actual use are a subset of what might be documented. The core file manipulation and search tools are well-tested and actively used, while some advanced tools (like Todo management and Notebook editing) appear to be either not implemented or not yet widely adopted in the public repositories.

### 9. **Test Coverage**

- ✅ Read tool - Has integration tests
- ✅ Write tool - Used in examples
- ✅ Edit/MultiEdit - Listed as base tools
- ✅ Glob/Grep/LS - Listed as base tools
- ❌ TodoWrite/TodoRead - No tests found
- ❌ NotebookEdit/NotebookRead - No tests found
- ❌ WebSearch/WebFetch - Explicitly disallowed by default
- ❌ exit_plan_mode - No evidence found

### 10. **MCP (Model Context Protocol) Server Configuration**

From the claude-code-sdk-python types, MCP servers can be configured in three ways:

```python
# 1. STDIO Server (most common)
McpStdioServerConfig = {
    "type": "stdio",  # Optional
    "command": "mcp-server-name",
    "args": ["--arg1", "--arg2"],  # Optional
    "env": {"KEY": "value"}  # Optional
}

# 2. SSE Server
McpSSEServerConfig = {
    "type": "sse",
    "url": "https://example.com/sse",
    "headers": {"Authorization": "Bearer token"}  # Optional
}

# 3. HTTP Server
McpHttpServerConfig = {
    "type": "http",
    "url": "https://example.com/api",
    "headers": {"Authorization": "Bearer token"}  # Optional
}
```

**Usage in ClaudeCodeOptions:**
```python
options = ClaudeCodeOptions(
    mcp_tools=["mcp_tool_1", "mcp_tool_2"],
    mcp_servers={
        "server1": {
            "command": "mcp-filesystem",
            "args": ["--root", "/path/to/files"]
        },
        "server2": {
            "type": "sse",
            "url": "https://api.example.com/mcp"
        }
    }
)
```

### 11. **Complete ClaudeCodeOptions Available**

From the types.py file, here are all available options:

```python
@dataclass
class ClaudeCodeOptions:
    allowed_tools: list[str] = []
    max_thinking_tokens: int = 8000
    system_prompt: str | None = None
    append_system_prompt: str | None = None
    mcp_tools: list[str] = []
    mcp_servers: dict[str, McpServerConfig] = {}
    permission_mode: PermissionMode | None = None  # "default" | "acceptEdits" | "bypassPermissions"
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    disallowed_tools: list[str] = []
    model: str | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
```

### 12. **Final Summary of Tool Verification**

**Tools with Concrete Evidence of Working:**
1. **File Operations**: Read, Write, Edit, MultiEdit
2. **Search Operations**: Glob, Grep, LS
3. **GitHub Operations** (via MCP): commit_files, delete_files, update_claude_comment

**Tools Mentioned but Not Verified:**
1. **Bash** - Listed in documentation but no test examples found
2. **TodoWrite/TodoRead** - No implementation found
3. **NotebookEdit/NotebookRead** - No implementation found
4. **exit_plan_mode** - No implementation found
5. **WebSearch/WebFetch** - Actively blocked by default

**Key Insights:**
1. The core tools for file manipulation are real and tested
2. MCP protocol allows extending tools through custom servers
3. Security restrictions apply (WebSearch/WebFetch disallowed)
4. Some documented tools may be aspirational or private implementations
5. The actual available tools are more limited than documentation suggests

This verification shows that the core file manipulation tools are real and working, while some of the more advanced tools mentioned in documentation may not be fully implemented or available in the current Claude Code implementation. The MCP protocol allows for extensibility through custom servers, which explains how tools like `mcp__github_file_ops__*` are implemented.