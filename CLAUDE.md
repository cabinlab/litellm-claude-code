# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a LiteLLM Claude Code Provider that creates an OpenAI-compatible API interface for Claude models using the Claude Code SDK. It bridges Claude's capabilities to applications expecting OpenAI API format, using OAuth authentication instead of API keys.

## High-Level Architecture

The project implements a custom LiteLLM provider that:
1. Receives OpenAI-format API requests on port 4000
2. Translates them to Claude Code SDK calls using OAuth authentication
3. Returns responses in OpenAI-compatible format
4. Supports streaming, all Claude models, and standard chat completions

Key components:
- `claude_code_provider.py`: Custom LiteLLM provider implementing the bridge
- `config/litellm_config.yaml`: Model mappings and configuration
- `custom_handler.py`: Exposes provider for YAML configuration
- Docker-based deployment with PostgreSQL for state management

## Common Development Commands

### Docker Operations
```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs litellm

# Restart after config changes
docker-compose restart litellm

# Authenticate Claude (OAuth flow)
./scripts/authenticate-claude.sh
# or directly:
docker exec -it litellm-claude-litellm-1 claude-code login
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
pip install git+https://github.com/arthurcolle/claude-code-sdk-python.git

# Run locally
export PYTHONPATH=".:$PYTHONPATH"
litellm --config config/litellm_config.yaml --port 4000
```

### Testing
```bash
# Test with curl
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234" \
  -d '{"model": "sonnet", "messages": [{"role": "user", "content": "Hello"}]}'

# List available models
curl http://localhost:4000/v1/models -H "Authorization: Bearer sk-1234"

# Run test scripts
python test_openai_client.py
python test_provider.py
```

## Available Models

- `sonnet` - Claude Sonnet 4
- `opus` - Claude Opus 4
- `claude-3-5-haiku-20241022` - Claude 3.5 Haiku
- `default` - Default model with automatic fallback

## Key Configuration Files

- `config/litellm_config.yaml`: Model definitions and custom provider mapping
- `docker-compose.yml`: Container orchestration with LiteLLM and PostgreSQL
- `.env`: Environment variables (minimal, uses OAuth)
- `Dockerfile`: Multi-stage build with Node.js and Python dependencies

## API Configuration

- Base URL: `http://localhost:4000/v1`
- Authorization: `Bearer sk-1234`
- Endpoints: `/chat/completions`, `/models`, `/health`
- Supports both sync and async streaming

## Development Workflow

1. Modify provider code in `claude_code_provider.py`
2. Update model configurations in `config/litellm_config.yaml`
3. Restart container: `docker-compose restart litellm`
4. Test changes with curl or test scripts
5. OAuth tokens persist in container at `/root/.claude.json`

The project uses no linting or formatting tools - follow existing code style when making changes.