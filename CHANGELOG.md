# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-07-19

### Added
- Initial release of LiteLLM Claude Code Provider
- Custom LiteLLM provider implementation for Claude Code SDK
- Support for all Claude models (Opus, Sonnet, Haiku) via OpenAI-compatible API
- OAuth authentication support for Claude Pro/Max users
- Docker-based deployment with automated image publishing
- Web UI for testing at `localhost:4000/ui/`

### Features
- OpenAI API compatibility for Claude models
- Auth persists across container restarts
- Support for both OAuth (Claude subscription) tokens and API keys
- Multi-platform Docker images (amd64/arm64)

### Notes
- This is an early release and has not been tested with LiteLLM-compatible clients
- Streaming support is partial due to Claude Code SDK limitations

[0.1.0]: https://github.com/cabinlab/litellm-claude-code/releases/tag/v0.1.0