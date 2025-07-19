# Comprehensive Claude Code SDK Verification Summary

## Overview

Five specialized agents conducted parallel investigations to verify all claims about the Claude Code SDK. This document summarizes their definitive findings based on source code analysis of the `anthropics/claude-code-sdk-python` repository.

## Verification Results by Category

### 1. Core Parameters (Agent 1) ✓ VERIFIED

**All standard LLM parameters are NOT supported:**

| Parameter | Supported | Evidence |
|-----------|-----------|----------|
| temperature | ❌ | Not in ClaudeCodeOptions class |
| max_tokens | ❌ | Not in ClaudeCodeOptions class |
| stop_sequences | ❌ | Not in ClaudeCodeOptions class |
| top_p | ❌ | Not in ClaudeCodeOptions class |
| top_k | ❌ | Not in ClaudeCodeOptions class |

**Key Finding**: The SDK operates at a different abstraction level than the Anthropic API, focusing on code assistance rather than text generation control.

### 2. SDK-Specific Features (Agent 2) ✓ VERIFIED

**All SDK features are FULLY SUPPORTED:**

| Feature | Supported | CLI Flag | Type |
|---------|-----------|----------|------|
| allowed_tools | ✅ | --allowedTools | list[str] |
| permission_mode | ✅ | --permission-mode | PermissionMode |
| cwd | ✅ | (subprocess cwd) | str \| Path |
| max_turns | ✅ | --max-turns | int |
| system_prompt | ✅ | --system-prompt | str |

**Additional Features Found**:
- `append_system_prompt`
- `disallowed_tools`
- `mcp_servers` and `mcp_tools`
- `continue_conversation` and `resume`
- `max_thinking_tokens`

### 3. Advanced Features (Agent 3) ✓ VERIFIED

**None of these advanced features are supported:**

| Feature | Supported | Why Not |
|---------|-----------|---------|
| OpenAI-style function calling | ❌ | SDK uses predefined tools only |
| Vision/image input | ❌ | Text-only, no multimodal support |
| Web search | ❌ | Focuses on local file operations |
| JSON response format | ❌ | No output schema control |

**Key Distinction**: `allowed_tools` refers to Claude Code's built-in tools (Read, Write, Bash), not custom function definitions.

### 4. Token Usage & Models (Agent 4) ⚠️ CORRECTION NEEDED

**Important Discovery**: Token usage is NOT estimates!

| Claim | Original | Verified | Evidence |
|-------|----------|----------|----------|
| Token usage | "estimates only" | **ACTUAL API DATA** | ResultMessage.usage contains real counts |
| Model selection | ✅ | ✅ | Fully supported via --model flag |

**Supported Models**:
- Claude Opus 4: `claude-opus-4-20250514`
- Claude Sonnet 4: `claude-sonnet-4-20250514`
- Claude Haiku 3.5: `claude-3-5-haiku-20241022`
- All legacy models (3.7, 3.5, 3.0 variants)

### 5. Authentication (Agent 5) ✓ VERIFIED

**OAuth-only authentication confirmed:**

| Method | Supported | Evidence |
|--------|-----------|----------|
| OAuth (CLI login) | ✅ | Only method supported |
| API Keys | ❌ | Zero references in codebase |
| ANTHROPIC_API_KEY | ❌ | Not used by SDK |

**GitHub Issue #1084** confirms users with API keys cannot use Claude Code - this is by design.

## Key Corrections to Original Investigation

1. **Token Usage**: The SDK returns REAL token counts from the API, not estimates. The `ResultMessage.usage` field contains:
   - `input_tokens`
   - `output_tokens` 
   - `cache_read_input_tokens`
   - `cache_creation_input_tokens`
   - Additional metrics

2. **Additional SDK Features**: Found 8+ more supported parameters beyond the original 4 identified.

## Implications for LiteLLM Provider

### Must Update:
1. Remove fake token usage - use actual data from ResultMessage
2. Add all supported SDK parameters (not just the 4 originally identified)
3. Document that standard LLM parameters will be ignored

### Architecturally Correct:
1. OAuth-only approach
2. Message-level streaming (already verified)
3. Model pass-through implementation

## Conclusion

The multi-agent verification confirms most original claims with two important corrections:
1. Token usage is real API data, not estimates
2. More SDK features exist than originally documented

The Claude Code SDK is definitively NOT a drop-in replacement for the Anthropic API but rather a specialized tool for code assistance with its own parameter set and authentication model.