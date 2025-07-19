# LiteLLM Claude Code Provider

A generic LiteLLM provider that makes Claude Code SDK available through the standard OpenAI-compatible API interface. Based on Anthropic's official [Claude Code LLM Gateway](https://docs.anthropic.com/en/docs/claude-code/llm-gateway) docs.

## Features

- ✅ **Claude Pro/Max Plan**: Uses Claude Code's OAuth authentication (no API keys needed)
- ✅ **Claude Code <--> OpenAI Key**: Use Claude Code in apps expecting OpenAI API keys
- **Docker Deployment**: LiteLLM + Claude Code in single container
- **Model Selection**: Supports all Claude models [ ***Opus*** | ***Sonnet*** | ***Haiku*** ]
- **Standard Interface**: Drop-in replacement for OpenAI API
- **Configurable**: Update models without code changes

## Quick Start

### Prerequisites
- Docker and Docker Compose
- A master key for API authentication (required)

### Setup

1. **Set your main key** (REQUIRED - see [docs/SECURITY.md](docs/SECURITY.md)):
   ```bash
   # LiteLLM requires these keys to start with with 'sk-'
   
   # For development, DIY a simple key 
   export LITELLM_MASTER_KEY="sk-dev-test-key"

   # Or generate a secure key
   export LITELLM_MASTER_KEY="sk-$(openssl rand -hex 32)"

   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. **Authenticate Claude** (first-time only):
   
   Using Docker exec to authenticate:
   ```bash
   # Enter the container
   docker exec -it litellm-claude-litellm-1 /bin/bash
   
   # Run claude to check authentication (will prompt if needed)
   claude
   
   # Follow the prompts to authenticate via Pro/Max Plan (API might still work?)
   
   # Exit the container
   exit
   ```
   
   - ~~Navigate to `http://localhost:4000/auth`~~
   - ~~Click "Start Authentication"~~
   - ~~Follow the OAuth flow in your browser~~
   - ~~See [AUTH_SETUP.md](AUTH_SETUP.md) for detailed instructions~~

4. The API is now available at `http://localhost:4000/v1`

### Use with OpenAI Python Client

```python
import openai

client = openai.OpenAI(
    api_key="sk-your-master-key",
    base_url="http://localhost:4000/v1"
)

response = client.chat.completions.create(
    model="claude-sonnet",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.choices[0].message.content)
```

## Available Models

| Model Name | Description |
|------------|-------------|
| `sonnet` | Claude Sonnet (latest version) |
| `opus` | Claude Opus (latest version) |
| `default` | Default Claude model |
| `default` | Haiku |


## Configuration

Edit `config/litellm_config.yaml` to add/modify models:

```yaml
model_list:
  - model_name: my-new-model
    litellm_params:
      model: claude-code-sdk/claude-4-new-model
```

Restart the container: `docker-compose restart litellm`

## Integration Examples

### With any LiteLLM-compatible application

Set environment variables:
```bash
export OPENAI_BASE_URL="http://localhost:4000/v1"
export OPENAI_API_KEY="sk-dummy"
```

### With LangChain

```python
from langchain.llms import OpenAI

llm = OpenAI(
    openai_api_base="http://localhost:4000/v1",
    openai_api_key="sk-dummy",
    model_name="claude-sonnet"
)
```

### With Applications expecting OpenAI API

* Any application that uses the OpenAI API format can now use Claude models through this provider.
* Works best with applications using structured responses. Streaming works -ish

## Authentication

This provider uses Claude CLI OAuth authentication:
- First-time setup requires browser-based OAuth flow
- ~~Authentication is handled through the integrated web UI at `/auth`~~
- Credentials persist in Docker volume across container restarts
- No API keys needed - uses Pro/Max Plan (OAuth tokens)

See [AUTH_SETUP.md](AUTH_SETUP.md) for detailed authentication instructions.

### Adding New Models

1. Edit `config/litellm_config.yaml`
2. Add model entry with appropriate Claude model name
3. Restart the service

## Architecture

```
Client Application → LiteLLM Proxy → Claude Code SDK Provider → Claude Code SDK → Claude API
```

The provider:
1. Receives OpenAI-format requests from LiteLLM
2. Converts messages to Claude prompt format
3. Extracts model name and creates `ClaudeCodeOptions(model=...)`
4. Calls Claude Code SDK with OAuth authentication
5. Returns response in OpenAI format

## Troubleshooting

### Test with curl

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-master-key" \
  -d '{
    "model": "claude-sonnet",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### "Authentication failed"
- Ensure running inside Claude Code environment
- Check that `CLAUDE_CODE_SESSION` environment variable is set

### "Model not found"
- Check model name in `config/litellm_config.yaml`
- Verify model name matches available Claude models

## License

MIT License