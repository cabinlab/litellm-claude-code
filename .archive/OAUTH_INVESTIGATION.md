# OAuth Investigation for Claude Code in Docker

## Current Status

We've discovered a fundamental disconnect between the Claude Code SDK's OAuth system and the Claude CLI's authentication requirements.

## Key Findings

1. **SDK Has Its Own OAuth Implementation**:
   - The SDK's `claude-auth` command implements a complete OAuth flow
   - Opens browser, runs callback server, exchanges code for tokens
   - Stores OAuth tokens in `~/.claude_code/tokens.json`
   - This is completely separate from the CLI's authentication

2. **The Fundamental Disconnect**:
   - The SDK uses the Claude CLI as a subprocess for all operations
   - The SDK tries to pass its OAuth tokens as `ANTHROPIC_API_KEY: Bearer <token>`
   - The CLI doesn't accept OAuth tokens in this format
   - As noted in the code: "The CLI would need to be modified to support OAuth tokens"
   - The CLI requires its own authentication (stored in `~/.claude/.credentials.json`)

3. **The Core Problem**:
   - The CLI requires interactive authentication (browser-based OAuth)
   - Docker containers can't perform interactive auth flows
   - The SDK can't bypass the CLI's authentication requirements
   - We need the CLI to be pre-authenticated before the SDK can use it

## Working Solution

By mounting the host's `~/.claude` directory (not just `~/.claude.json`), we can share the CLI's OAuth credentials with the container. The key file is `~/.claude/.credentials.json` which contains the OAuth tokens from the CLI's interactive authentication.

### Confirmed Working:
- ✅ Sonnet model
- ✅ Opus model
- ✅ Haiku model: requires full `claude-3-5-haiku-20241022`, not `haiku`

### Model Names:
- `sonnet`, `opus`, and `default` are aliases for the latest versions (like `:latest` tags)
- Haiku requires exact model name specification (e.g., `claude-3-5-haiku-20241022`)
- TODO: Check for updated haiku model name when re-enabled upstream
- You could probably customize this to use older Sonet and Opus models

## Potential Production Solutions

### Option A: Pre-Authentication Container
Create a special container that can be run interactively:
```bash
docker run -it -v claude-auth:/root litellm-claude auth
```
This would:
- Run with TTY for interactive auth
- Store credentials in a Docker volume
- Main container uses the same volume

### Option B: OAuth Proxy Service
Run a separate service on the host that:
- Handles OAuth flow with browser access
- Provides tokens to containers via API
- Manages token refresh automatically

### Option C: Environment Token Injection
- Authenticate on host with Claude CLI
- Extract tokens from CLI's internal storage
- Pass tokens as environment variables to container
- Container configures CLI to use these tokens

## Next Steps

1. Investigate where Claude CLI actually stores OAuth tokens
2. Determine if tokens can be extracted and reused
3. Test if CLI accepts tokens via environment variables
4. Implement the most viable solution

## Testing Commands

```bash
# Check auth status in container
docker exec litellm-claude-litellm-1 claude auth status

# Test API with current setup
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234" \
  -d '{"model": "sonnet", "messages": [{"role": "user", "content": "Hello"}]}'
```