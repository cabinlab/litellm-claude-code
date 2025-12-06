# Claude Code Tools - Official Documentation Search Results

## Search Summary

This report documents the official list of Claude Code tools based on authoritative sources from Anthropic's documentation and repositories.

## Official Claude Code Tools List

Based on the official Anthropic documentation at https://docs.anthropic.com/en/docs/claude-code/settings, here are the **available tools in Claude Code**:

### Core Tools (Built-in)

1. **Agent**
   - Description: Runs a sub-agent to handle complex, multi-step tasks
   - Permission Required: No
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

2. **Bash**
   - Description: Executes shell commands in your environment
   - Permission Required: Yes
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

3. **Edit**
   - Description: Makes targeted edits to specific files
   - Permission Required: Yes
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

4. **Glob**
   - Description: Finds files based on pattern matching
   - Permission Required: No
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

5. **Grep**
   - Description: Searches for patterns in file contents
   - Permission Required: No
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

6. **LS**
   - Description: Lists files and directories
   - Permission Required: No
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

7. **MultiEdit**
   - Description: Performs multiple edits on a single file atomically
   - Permission Required: Yes
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

8. **NotebookEdit**
   - Description: Modifies Jupyter notebook cells
   - Permission Required: Yes
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

9. **NotebookRead**
   - Description: Reads and displays Jupyter notebook contents
   - Permission Required: No
   - Source: https://docs.anthropic.com/en/docs/claude-code/settings

10. **Read**
    - Description: Reads the contents of files
    - Permission Required: No
    - Source: https://docs.anthropic.com/en/docs/claude-code/settings

11. **TodoRead**
    - Description: Reads the current session's task list
    - Permission Required: No
    - Source: https://docs.anthropic.com/en/docs/claude-code/settings

12. **TodoWrite**
    - Description: Creates and manages structured task lists
    - Permission Required: No
    - Source: https://docs.anthropic.com/en/docs/claude-code/settings

13. **WebFetch**
    - Description: Fetches content from a specified URL
    - Permission Required: Yes
    - Source: https://docs.anthropic.com/en/docs/claude-code/settings

14. **WebSearch**
    - Description: Performs web searches with domain filtering
    - Permission Required: Yes
    - Source: https://docs.anthropic.com/en/docs/claude-code/settings

15. **Write**
    - Description: Creates or overwrites files
    - Permission Required: Yes
    - Source: https://docs.anthropic.com/en/docs/claude-code/settings

## Tool Categories

### No Permission Required (Read-only)
- Agent
- Glob
- Grep
- LS
- NotebookRead
- Read
- TodoRead

### Permission Required (Write/Execute)
- Bash
- Edit
- MultiEdit
- NotebookEdit
- TodoWrite
- WebFetch
- WebSearch
- Write

## CLI Configuration with --allowedTools

According to the official documentation and web search results:

1. **CLI Flag Usage**: `claude --allowedTools <tool1>,<tool2>`
   - Example: `claude --allowedTools Edit,Read,Write`
   - Used for temporary, throw-away sessions

2. **Permission Syntax**:
   - `ToolName` - permit every action
   - `ToolName(*)` - permit any argument
   - `ToolName(filter)` - permit matching calls only
   - Examples:
     - `Edit`
     - `ReadFile:*`
     - `WriteFile(src/*)`
     - `Bash(ls *)`
     - `Bash(git commit:*)`
     - `Bash(npm install)`

3. **Configuration Methods**:
   - Interactive prompt: Click "Always allow" when Claude asks
   - Chat command: `/allowed-tools add Edit`
   - Config file: `.claude/settings.json` (project) or `~/.claude.json` (global)
   - CLI flag: `claude --allowedTools Edit` (temporary session)

## MCP (Model Context Protocol) Tools

Claude Code also supports MCP tools which follow the naming convention:
- Format: `mcp__<serverName>__<toolName>`
- Example: `mcp__filesystem__read_file`
- Must be explicitly allowed using --allowedTools

## Security Architecture

From the documentation:
1. **Default Behavior**: Tools requiring permission will prompt the user
2. **Policy Files**:
   - macOS: `/Library/Application Support/ClaudeCode/policies.json`
   - Linux: `/etc/claude-code/policies.json`
3. **Decision Sources**: 
   - "config" - from configuration files
   - "user_permanent" - user selected "Always allow"
   - "user_temporary" - user selected "Allow once"
   - "user_abort" - user aborted
   - "user_reject" - user rejected

## Comparison with SDK Findings

The official documentation confirms all tools found in the SDK investigation:
- ✅ All 15 tools from SDK are documented
- ✅ Permission requirements match SDK implementation
- ✅ Tool descriptions align with SDK functionality
- ✅ Additional configuration details provided (CLI flags, MCP support)

## Sources
1. Official Documentation: https://docs.anthropic.com/en/docs/claude-code/settings
2. Official Documentation: https://docs.anthropic.com/en/docs/claude-code/iam
3. Official Documentation: https://docs.anthropic.com/en/docs/claude-code/sdk
4. Official Repository: https://github.com/anthropics/claude-code
5. Web Search Results for CLI usage and configuration

## Conclusion

The official Claude Code tool list consists of 15 built-in tools, with clear permission boundaries between read-only operations (7 tools) and operations requiring explicit permission (8 tools). The --allowedTools CLI flag provides flexible, temporary permission management for command-line usage.