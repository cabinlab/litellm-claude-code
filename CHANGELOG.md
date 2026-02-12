# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-02-11

### Changed
- **BREAKING: Complete rewrite targeting Claude Agent SDK**
  - Replaced `claude-code-sdk` with `claude-agent-sdk`
  - `ClaudeCodeOptions` -> `ClaudeAgentOptions`
  - Provider prefix: `claude-code-sdk/` -> `claude-agent-sdk/`
- Rewrote provider as single clean implementation (was duplicate files)
- Simplified entrypoint: single script replaces multi-file chain
- Removed startup.py -- LiteLLM CLI handles server startup directly
- Greenfield requirements.txt -- dropped unused dependencies

### Removed
- Dockerfile.legacy
- Duplicate custom_handler.py files (root, config/, providers/)
- HTTP-only Open WebUI compose variant
- startup.py

## [0.1.0] - 2025-07-19

### Added
- Custom LiteLLM provider for Claude Code SDK with OpenAI API compatibility
- Support for all Claude models (Opus, Sonnet, Haiku)
- OAuth authentication for Claude Pro/Max users (persists across restarts)
- Docker-based deployment with multi-platform images (amd64/arm64)
- Web UI for testing at `localhost:4000/ui/`
- Streaming response support (partial, due to Claude Code SDK limitations)

[0.2.0]: https://github.com/cabinlab/litellm-claude-code/releases/tag/v0.2.0
[0.1.0]: https://github.com/cabinlab/litellm-claude-code/releases/tag/v0.1.0