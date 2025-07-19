# Claude Code SDK Parameter Investigation Summary

## Investigation Completed: Core LLM Parameters

### Files Created:
1. **agent1-core-parameters.md** - Comprehensive investigation report
2. **verify_parameters.py** - Python script to verify findings

### Key Findings:

The Claude Code SDK does **NOT** support any of the following standard LLM parameters:
- ❌ temperature
- ❌ max_tokens  
- ❌ stop_sequences
- ❌ top_p
- ❌ top_k

### Evidence Sources Examined:
1. **GitHub Repository**: anthropics/claude-code-sdk-python
   - `src/claude_code_sdk/types.py` - ClaudeCodeOptions definition
   - `src/claude_code_sdk/_internal/transport/subprocess_cli.py` - Command building
   - All examples and tests
   
2. **Official Documentation**: https://docs.anthropic.com/en/docs/claude-code/sdk
   - No mention of these parameters

### What the SDK DOES Support:
- `allowed_tools` - List of allowed tools
- `max_thinking_tokens` - Different from max_tokens
- `system_prompt` - System prompt
- `append_system_prompt` - Additional system prompt
- `mcp_tools` - MCP tool list
- `mcp_servers` - MCP server configurations
- `permission_mode` - Permission handling mode
- `continue_conversation` - Continue existing conversation
- `resume` - Resume from session ID
- `max_turns` - Maximum conversation turns
- `disallowed_tools` - List of disallowed tools
- `model` - Model selection
- `permission_prompt_tool_name` - Custom permission tool
- `cwd` - Working directory

### Conclusion:
The Claude Code SDK is designed for interactive code assistance and tool use, not for fine-grained control over text generation parameters. It operates at a higher abstraction level than the standard Anthropic API.