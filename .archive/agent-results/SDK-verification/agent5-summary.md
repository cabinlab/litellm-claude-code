# Claude Code SDK Authentication - Key Findings Summary

## ✅ Verified Claims

1. **SDK uses OAuth authentication (NOT API keys)** ✓
   - No API key support in the codebase
   - All authentication handled by Claude Code CLI

2. **Authentication happens via `claude-code login`** ✓
   - Actually just `claude` command (not `claude-code`)
   - OAuth flow with console.anthropic.com

3. **No support for ANTHROPIC_API_KEY** ✓
   - Zero references in the entire codebase
   - No environment variable handling for API keys

4. **Fundamental architectural difference from Anthropic API** ✓
   - Anthropic API: Direct API access with keys
   - Claude Code SDK: CLI subprocess proxy with OAuth

## 🔍 Key Evidence

### From Source Code
```python
# SDK spawns CLI subprocess - no auth handling
cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]

# No auth params in public API
async def query(*, prompt: str, options: ClaudeCodeOptions | None = None)

# No api_key field in options
ClaudeCodeOptions = (system_prompt, tools, model, etc.)  # No auth fields
```

### Authentication Flow
```
User → claude login → OAuth → Credentials stored → SDK uses CLI → CLI uses stored auth
```

## 📋 Quick Reference

| What | Where | How |
|------|-------|-----|
| Auth Method | OAuth only | Via Claude Code CLI |
| Login Command | `claude` | Opens browser for OAuth |
| Credentials | `~/.claude.json` | Managed by CLI |
| API Keys | Not supported | Use Anthropic API directly |
| SDK Role | CLI wrapper | No auth handling |

## 🚫 What Doesn't Work

- Setting `ANTHROPIC_API_KEY` - ignored by SDK
- Passing API keys programmatically - not possible
- Headless/CI authentication - requires pre-auth
- Multiple auth contexts - single CLI session only
- Enterprise API keys - Claude Code cannot use them (GitHub #1084)

## 💡 Real-World Impact

**GitHub Issue #1084**: "Employer provided me with an Anthropic API key to use Claude Code but there's no way to configure this key"
- Confirms API keys are NOT supported by design
- Enterprise users with API keys must use Anthropic API directly
- No workaround exists for using API keys with Claude Code