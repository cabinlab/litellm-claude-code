# LiteLLM Claude Code Provider

[![Build and Publish](https://github.com/cabinlab/litellm-claude-code/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/cabinlab/litellm-claude-code/actions/workflows/build-and-publish.yml)

A LiteLLM provider that makes Claude Code SDK available through the standard OpenAI-compatible API interface. Based on Anthropic's official [Claude Code LLM Gateway](https://docs.anthropic.com/en/docs/claude-code/llm-gateway) docs based on our:

 - [Claude Code SDK Docker images](https://github.com/cabinlab/claude-code-sdk-docker)

## Available Image

```bash
docker pull ghcr.io/cabinlab/litellm-claude-code:latest
```

## Features

- ✅ **Claude Pro/Max Plan**: Uses Claude Code's OAuth authentication (no API keys needed)
- ✅ **OpenAI API Compatibility**: Use Claude Code in apps expecting OpenAI API keys
- ✅ **Docker Deployment**: LiteLLM + Claude Code SDK in a single container
- ✅ **Model Selection**: Supports all Claude models (Opus, Sonnet, Haiku)
- ✅ **Standard Interface**: Drop-in replacement for OpenAI API

## Quick Start (Claude Pro/Max Users)

### Prerequisites
- Docker
- Claude Pro or Max subscription OR Anthropic API key

### Setup

1. **Download the configuration files**:
   ```bash
   # Create a directory for the project
   mkdir litellm-claude-code && cd litellm-claude-code
   
   # Download docker-compose.yml
   curl -O https://raw.githubusercontent.com/cabinlab/litellm-claude-code/main/docker-compose.yml
   
   # Download .env.example
   curl -o .env https://raw.githubusercontent.com/cabinlab/litellm-claude-code/main/.env.example
   ```

   Or if you prefer to clone the repository:
   ```bash
   git clone https://github.com/cabinlab/litellm-claude-code.git
   cd litellm-claude-code
   cp .env.example .env
   ```

3. **Set your master key** (REQUIRED):
   ```bash
   # Edit .env and update LITELLM_MASTER_KEY
   # For development, change to something like sk-9umbers-and-letters-and-junk
   LITELLM_MASTER_KEY=sk-your-desired-custom-key
   
   # For production, generate a secure key:
   LITELLM_MASTER_KEY=sk-$(openssl rand -hex 32)
   ```

4. **Get your Claude OAuth token** (wherever you have Claude Code installed):
   ```bash
   # If you don't have the Claude CLI installed:
   npm install -g @anthropic-ai/claude-code
   
   # Generate a long-lived token
   claude setup-token

   # Follow the web-based auth flow and copy the token that starts with
   sk-ant-oat01-
   ```


5. **Add the token to your .env file**:
   ```bash
   # Edit .env and add your token:
   CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-your-token-here
   ```

6. **Start the services**:
   ```bash
   docker-compose up -d
   ```

7. **Verify it's working**:

   ### Web UI
   Navigate to `http://localhost:4000/ui/` and click "Test Key" to try the interactive interface:

   ![LiteLLM Web UI Test Interface](docs/images/litellm-web-ui-test-key.png)

   ### Terminal
   ```bash
   # Check health (replace with your LITELLM_MASTER_KEY)
   curl http://localhost:4000/health -H "Authorization: Bearer sk-your-desired-custom-key"
   
   # List models
   curl http://localhost:4000/v1/models -H "Authorization: Bearer sk-your-desired-custom-key"
   ```

The API is now available at `http://localhost:4000/v1`

## Usage Examples

### OpenAI Python Client

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-desired-custom-key",  # Your LITELLM_MASTER_KEY from .env
    base_url="http://localhost:4000/v1"
)

response = client.chat.completions.create(
    model="sonnet",
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-desired-custom-key" \
  -d '{
    "model": "sonnet",
    "messages": [
      {"role": "user", "content": "Hello, Claude!"}
    ]
  }'
```

### LangChain

```python
from langchain.llms import OpenAI

llm = OpenAI(
    openai_api_base="http://localhost:4000/v1",
    openai_api_key="sk-your-desired-custom-key",
    model_name="sonnet"
)

response = llm("Tell me a joke")
print(response)
```

## Available Models

| Model Name | Description |
|------------|-------------|
| `sonnet` | Claude Sonnet (latest) |
| `opus` | Claude Opus (latest) |
| `claude-3-5-haiku-20241022` | Claude 3.5 Haiku |
| `default` | Starts with Opus, falls back to Sonnet |


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

### Authentication Methods

1. **Long-lived OAuth Tokens** (Recommended for Claude Pro/Max users)
   - Generate with `claude setup-token` on your host machine
   - Set `CLAUDE_CODE_OAUTH_TOKEN` in your `.env` file
   - Tokens start with `sk-ant-oat01-` and last for 1 year
   - Authentication persists across container restarts via Docker volume

2. **Interactive Authentication** (Alternative)
   ```bash
   # Enter the container
   docker exec -it litellm-claude-litellm-1 bash
   
   # Run claude to authenticate
   claude
   
   # Follow the browser authentication flow
   ```

3. **Anthropic API Keys**
   - Can set `ANTHROPIC_API_KEY` in `.env`
   - May override Pro/Max subscription benefits
   - Uses API credits instead of subscription

### Authentication Persistence

The Docker setup includes a named volume for authentication:
```yaml
volumes:
  - claude-auth:/home/claude/.claude
```

This ensures authentication persists across container restarts.

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

### Common Issues

**"Invalid API key" or 401 Unauthorized**
- Ensure you're using your `LITELLM_MASTER_KEY` value (not the OAuth token)
- The master key must start with `sk-`
- Check your Authorization header: `Bearer sk-your-desired-custom-key`

**"Authentication failed" from Claude SDK**
- Your OAuth token may have expired
- Regenerate with `claude setup-token` on your host machine
- Update `CLAUDE_CODE_OAUTH_TOKEN` in your `.env` file
- Restart the container: `docker-compose restart litellm`

**"Model not found"**
- Check available models: `curl http://localhost:4000/v1/models -H "Authorization: Bearer sk-your-desired-custom-key"`
- Valid model names: `sonnet`, `opus`, `claude-3-5-haiku-20241022`, `default`
- Model names are case-sensitive

**Slow responses or timeouts**
- The first request after startup may be slower while establishing connections
- Claude Code SDK responses can take 5-10 seconds for complex queries
- Consider increasing timeout values in your client application

### Testing the API

```bash
# Quick test
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-desired-custom-key" \
  -d '{
    "model": "sonnet",
    "messages": [{"role": "user", "content": "Say hello"}]
  }'

# With streaming (partial support)
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-desired-custom-key" \
  -d '{
    "model": "sonnet",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'
```

## Development

### Building Locally

If you want to build the image locally instead of using the pre-built image:

```bash
# Clone the repository
git clone https://github.com/cabinlab/litellm-claude-code.git
cd litellm-claude-code

# Build and run with docker-compose override
docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
```

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License