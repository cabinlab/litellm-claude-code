# Claude Code SDK Authentication Architecture Report

## Executive Summary

The Claude Code SDK uses **OAuth authentication via the Claude Code CLI** and does **NOT support API keys**. This is a fundamental architectural difference from the Anthropic API. The SDK acts as a Python wrapper around the Claude Code CLI tool, relying entirely on the CLI's authentication mechanisms.

## Key Findings

### 1. OAuth-Only Authentication

**Evidence from Source Code:**

From `subprocess_cli.py`:
```python
# The SDK spawns a subprocess to run the claude CLI command
cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]
# ... command building logic ...
self._process = await anyio.open_process(
    cmd,
    stdin=None,
    stdout=PIPE,
    stderr=PIPE,
    cwd=self._cwd,
    env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": "sdk-py"},
)
```

**Key Points:**
- No API key handling in the entire codebase
- No references to `ANTHROPIC_API_KEY` anywhere
- No authentication headers or tokens in the SDK code
- SDK communicates with Claude Code CLI via subprocess

### 2. CLI-Based Authentication Flow

**How It Works:**
1. User runs `claude` command to authenticate (OAuth flow)
2. CLI stores credentials locally (likely in `~/.claude.json`)
3. SDK spawns CLI subprocess which uses stored credentials
4. All authentication is handled by the CLI, not the SDK

**Evidence from Documentation:**
- The SDK requires Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
- No authentication parameters in the SDK API
- Error handling includes `CLINotFoundError` when CLI is not installed

### 3. No Direct API Key Support

**Source Code Analysis:**
```python
# From __init__.py - No authentication parameters
async def query(
    *, prompt: str, options: ClaudeCodeOptions | None = None
) -> AsyncIterator[Message]:
```

**ClaudeCodeOptions Type (from types.py):**
- No `api_key` field
- No authentication-related options
- Only contains functional parameters (system_prompt, tools, etc.)

### 4. Error Handling for Authentication Failures

**From _errors.py:**
```python
class CLINotFoundError(CLIConnectionError):
    """Raised when Claude Code is not found or not installed."""

class ProcessError(ClaudeSDKError):
    """Raised when the CLI process fails."""
```

**Authentication Error Scenarios:**
- If CLI not installed: `CLINotFoundError`
- If not authenticated: CLI process will fail with `ProcessError`
- No specific authentication error class (handled by CLI)

### 5. Authentication Options (via CLI)

**From Claude Code Documentation:**
1. **Anthropic Console (Default)**
   - OAuth flow with console.anthropic.com
   - Requires active billing

2. **Claude App Authentication**
   - Pro/Max plan users
   - Login with Claude.ai account

3. **Enterprise Platforms**
   - Amazon Bedrock
   - Google Vertex AI

### 6. Comparison with Anthropic API

| Feature | Anthropic API | Claude Code SDK |
|---------|---------------|-----------------|
| Authentication Method | API Keys | OAuth (via CLI) |
| Environment Variable | `ANTHROPIC_API_KEY` | None |
| Auth Headers | `x-api-key` | None (handled by CLI) |
| Credential Storage | User manages keys | CLI manages (~/.claude.json) |
| Direct API Access | Yes | No (via CLI proxy) |
| Programmatic Auth | Yes (pass API key) | No (manual CLI login) |

## Architecture Implications

### Security Benefits
1. No API keys in code or environment variables
2. OAuth provides better security and scoping
3. Credentials managed centrally by CLI
4. Automatic token refresh handled by CLI

### Limitations
1. Cannot programmatically authenticate
2. Requires manual `claude` login before SDK use
3. Cannot use in headless/CI environments without pre-authentication
4. No support for multiple authentication contexts in code

## Source Code Evidence

### No API Key References
Searching the entire repository reveals:
- Zero mentions of "api_key" or "api-key"
- Zero mentions of "ANTHROPIC_API_KEY"
- No authentication-related environment variables

### CLI Dependency
From GitHub Issue #24:
```
"Always see 'apiKeySource': '/login managed key' in the results"
```
This confirms the SDK uses CLI-managed authentication.

## Real-World Confirmation

From GitHub Issue #1084: "Employer provided me with an Anthropic API key to use Claude Code but there's no way to configure this key"
- Users with API keys **cannot use them with Claude Code**
- The issue remains open, confirming this is by design
- Claude Code team assigns this to "area:auth" and "area:api" labels

From GitHub Issue #630: Testing API key environment variables
- Setting `ANTHROPIC_API_KEY` does not work for Claude Code
- Multiple API keys cannot be used with different profiles
- OAuth credentials are shared globally, not per-profile

## Conclusion

The Claude Code SDK **definitively does not support API keys**. It operates as a thin Python wrapper around the Claude Code CLI, delegating all authentication to the CLI's OAuth-based system. This is a fundamental architectural choice that provides better security but less flexibility compared to traditional API key authentication.

Users must authenticate via `claude login` before using the SDK, and there is no programmatic way to provide credentials. This makes the SDK suitable for interactive development environments but challenging for automated/CI use cases without pre-configured authentication.

**Important Note for Enterprise Users**: Organizations that provide developers with Anthropic API keys cannot use Claude Code directly. They must either:
1. Use the Anthropic API directly (not Claude Code)
2. Set up individual OAuth authentication for each developer
3. Configure enterprise platforms (Bedrock/Vertex AI)