# Consolidated Claude Code Tools Investigation

## Executive Summary

Three agents investigated Claude Code tools from different angles: SDK source code, official documentation, and real usage examples. This consolidated report reconciles their findings to provide the definitive list of Claude Code tools.

## Confirmed Tool List (15 Tools)

Based on official documentation (Agent 2) with verification status from other agents:

### No Permission Required (7 tools)
| Tool | SDK | Docs | Examples | Description |
|------|-----|------|----------|-------------|
| **Agent** | ❌ | ✅ | ❌ | Runs sub-agents for complex tasks |
| **Glob** | ❌ | ✅ | ✅ | File pattern matching |
| **Grep** | ❌ | ✅ | ✅ | Pattern search in files |
| **LS** | ❌ | ✅ | ✅ | Lists files and directories |
| **NotebookRead** | ❌ | ✅ | ❌ | Reads Jupyter notebooks |
| **Read** | ✅ | ✅ | ✅ | Reads file contents |
| **TodoRead** | ❌ | ✅ | ❌ | Reads task lists |

### Permission Required (8 tools)
| Tool | SDK | Docs | Examples | Description |
|------|-----|------|----------|-------------|
| **Bash** | ✅ | ✅ | ❌ | Executes shell commands |
| **Edit** | ✅ | ✅ | ✅ | Makes targeted file edits |
| **MultiEdit** | ❌ | ✅ | ✅ | Multiple atomic file edits |
| **NotebookEdit** | ❌ | ✅ | ❌ | Modifies Jupyter notebooks |
| **TodoWrite** | ❌ | ✅ | ❌ | Manages task lists |
| **WebFetch** | ❌ | ✅ | ❌* | Fetches URL content |
| **WebSearch** | ❌ | ✅ | ❌* | Performs web searches |
| **Write** | ✅ | ✅ | ✅ | Creates/overwrites files |

*Note: WebFetch and WebSearch are explicitly disallowed by default in the Claude Code Action configuration

## Key Findings

### 1. SDK vs CLI Architecture
- The Python SDK only references 4 tools explicitly (Read, Write, Edit, Bash)
- The SDK is tool-agnostic - it passes tool names as strings to the CLI
- The actual tool implementations are in the Claude Code CLI binary

### 2. Tool Discovery Sources
- **Official Documentation**: Most authoritative - lists all 15 tools
- **SDK Code**: Only shows how tools are passed, not which exist
- **Usage Examples**: Limited - only file operations are commonly used

### 3. Important Discrepancies

#### WebSearch Availability
- **Documentation**: Lists WebSearch as available
- **Examples**: Shows WebSearch is disallowed by default
- **Resolution**: WebSearch EXISTS but requires explicit permission

#### Missing Test Coverage
Several documented tools have no test examples:
- Agent
- TodoRead/TodoWrite
- NotebookRead/NotebookEdit
- Bash (mentioned but not tested)

### 4. Tool Permission System

From the official documentation:
```bash
# CLI usage
claude --allowedTools Edit,Read,Write

# Configuration patterns
"ToolName"          # permit every action
"ToolName(filter)"  # permit matching calls only
"Bash(ls *)"       # permit only ls commands
```

### 5. MCP Extensions

Agent 3 discovered that Claude Code supports tool extensions via MCP:
- Additional tools can be added through MCP servers
- GitHub integration adds specialized tools
- This explains tools beyond the core 15

## Corrections to Previous Investigation

1. **WebSearch IS available** - Previous report incorrectly stated no web search
2. **Tools vs Functions** - Claude Code has built-in tools, not OpenAI-style function calling
3. **Tool Count** - 15 official tools, not just the 4 found in SDK

## Definitive Tool Categories

### Core File Operations
- Read, Write, Edit, MultiEdit

### Search & Navigation  
- Glob, Grep, LS

### Execution
- Bash, Agent

### Specialized
- TodoRead, TodoWrite
- NotebookRead, NotebookEdit

### Web Operations
- WebSearch, WebFetch

## Conclusion

The Claude Code SDK investigation initially underestimated available tools because:
1. The SDK only passes tool names, doesn't define them
2. Many tools lack test coverage
3. Some tools (WebSearch) are restricted by default

The official documentation provides the authoritative list of 15 built-in tools, with the possibility of extensions via MCP.