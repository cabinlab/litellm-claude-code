# LiteLLM Claude Agent SDK Provider


[![Discord](https://img.shields.io/badge/Discord-Join%20Community-7289da?logo=discord&logoColor=white)](https://discord.gg/aaSgZBgkCK) [![Build and Publish](https://github.com/cabinlab/litellm-claude-code/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/cabinlab/litellm-claude-code/actions/workflows/build-and-publish.yml)

Dockerized LiteLLM with custom provider that makes Claude Agent SDK available through the standard OpenAI-compatible API interface. Based on Anthropic's official [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-agent-sdk) documentation:

```mermaid
graph LR
    A["Claude Agent SDK<br/>OAuth/API"] <--> B["LiteLLM<br/>Translation"]
    B <--> C["Open WebUI, Graphiti,<br/>LangChain, etc."]
```

## Available Image

```bash
docker pull ghcr.io/cabinlab/litellm-claude-code:latest
```
based on our [Claude Code SDK Docker images](https://github.com/cabinlab/claude-code-sdk-docker)

## Features

- **Claude Pro/Max Plan**: Uses Claude's OAuth authentication (no API keys needed)
- **OpenAI API Compatibility**: Use Claude in apps expecting OpenAI API keys
- **Docker Deployment**: LiteLLM + Claude Agent SDK in a single container
- **Model Selection**: Supports all Claude models (Opus, Sonnet, Haiku)
- **Standard Interface**: Drop-in replacement for OpenAI API

## Quick Start (Claude Pro/Max Users)

### Prerequisites
- Docker
- Claude Pro or Max subscription OR Anthropic API key

### Setup

1. **Download the configuration files**:
   ```bash
   # Create a directory for the project
   mkdir litellm-claude && cd litellm-claude

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

2. **Set your master key** (REQUIRED):
   ```bash
   # Edit .env and update LITELLM_MASTER_KEY
   LITELLM_MASTER_KEY=sk-your-desired-custom-key
   ```

   See [Security Guide](docs/SECURITY.md) for key generation best practices

3. **Get your Claude OAuth token** (wherever you have Claude Code installed):
   ```bash
   # If you don't have the Claude CLI installed:
   npm install -g @anthropic-ai/claude-code

   # Generate a long-lived token
   claude setup-token

   # Follow the web-based auth flow and copy the token that starts with
   sk-ant-oat01-
   ```


4. **Add the token to your .env file**:
   ```bash
   # Edit .env and add your token:
   CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-your-token-here
   ```

5. **Start the services**:
   ```bash
   docker-compose up -d
   ```

6. **Verify it's working**:

   ### Web UI
   Navigate to `http://localhost:4000/ui/` and select Test Key:

   ![LiteLLM Web UI Test Interface](docs/images/litellm-web-ui-test-key.png)

   ### Terminal
   ```bash
   # Check health (replace with your LITELLM_MASTER_KEY)
   curl http://localhost:4000/health -H "Authorization: Bearer sk-your-desired-custom-key"

   # List models
   curl http://localhost:4000/v1/models -H "Authorization: Bearer sk-your-desired-custom-key"
   ```

The API is now available at `http://localhost:4000/v1`

## Available Models

| Model Name | Description |
|------------|-------------|
| `sonnet` | Claude Sonnet (latest) |
| `opus` | Claude Opus (latest) |
| `haiku` | Claude Haiku (latest) |

### Adding Models
The default settings automatically use the latest Sonnet, Opus, and Haiku models. You can try other models from [Anthropic's list](https://docs.anthropic.com/en/docs/about-claude/models/overview):

1. Edit `config/litellm_config.yaml` to add/modify models:

```yaml
model_list:
  - model_name: {model alias}
    litellm_params:
      model: claude-agent-sdk/{model-name}
```

2. Restart the container

```bash
docker-compose restart litellm
```

## Authentication

### Methods

1. **Long-lived OAuth Tokens** (Recommended for Claude Pro/Max users)
   - Generate with `claude setup-token` on your host machine
   - Set `CLAUDE_CODE_OAUTH_TOKEN` in your `.env` file
   - Tokens start with `sk-ant-oat01-`
   - Authentication persists across container restarts via Docker volume

2. **Interactive Authentication** (Alternative)
   <details>
   <summary>View steps</summary>

   ```bash
   # Enter the container
   docker exec -it litellm-claude-litellm-1 bash

   # Run claude to authenticate
   claude

   # Follow the browser authentication flow
   ```
   </details>

3. **Anthropic API Keys**
   <details>
   <summary>View details</summary>

   - Can set `ANTHROPIC_API_KEY` in `.env`
   - May override Pro/Max subscription benefits
   - Uses API credits instead of subscription
   </details>

### Authentication Persistence

The Docker setup includes a named volume for authentication:
```yaml
volumes:
  - claude-auth:/home/claude/.claude
```

This ensures authentication persists across container restarts.

## Architecture

```mermaid
graph LR
    A[Client App] --> B[LiteLLM Proxy]
    B --> C[Claude Agent SDK Provider]
    C --> D[Claude Agent SDK]
    D --> E[Claude API]
```

The provider:
1. Receives OpenAI-format requests from LiteLLM
2. Converts messages to Claude prompt format
3. Extracts model name and creates `ClaudeAgentOptions(model=...)`
4. Calls Claude Agent SDK with OAuth authentication
5. Returns response in OpenAI format

## Direct API Use

<details>
<summary>View Python example</summary>

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
</details>

See [Usage Examples](docs/USAGE-EXAMPLES.md) for more languages and frameworks (cURL, LangChain, JavaScript, Graphiti, etc.)

## Troubleshooting

<details>
<summary>View common issues and solutions</summary>

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
- Valid model names: `sonnet`, `opus`, `haiku`
- Model names are case-sensitive

**Slow responses or timeouts**
- The first request after startup may be slower while establishing connections
- Claude Agent SDK responses can take 5-10 seconds for complex queries
- Consider increasing timeout values in your client application

**WebSocket Connection Failed**
- Ensure you're accessing the page via HTTP (not HTTPS)
- Check that port 4000 is accessible
- Try refreshing the page

**OAuth Page Shows Error**
- This is normal - the CLI handles the callback internally
- Return to the terminal to continue authentication

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

</details>

## Building Locally

<details>
<summary>View build instructions</summary>

If you want to build the image locally instead of using the pre-built image:

```bash
# Clone the repository
git clone https://github.com/cabinlab/litellm-claude-code.git
cd litellm-claude-code

# Build and run with docker-compose override
docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
```

</details>

## License

MIT License
