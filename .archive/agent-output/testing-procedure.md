# Claude Code SDK Testing Procedure

## Overview

This document outlines the testing procedure to verify Claude Code SDK capabilities and validate our findings about supported/unsupported features.

## Prerequisites

1. **Install Claude Code SDK** (if not already installed):
   ```bash
   pip install claude-code-sdk
   npm install -g @anthropic-ai/claude-code
   ```

2. **Authenticate with Claude Code**:
   ```bash
   claude-code login
   ```

3. **Ensure Python environment has required packages**:
   ```bash
   pip install asyncio
   ```

## Testing Steps

### 1. Run Automated Test Suite

Execute the comprehensive test script:

```bash
cd /home/andrew/litellm-claude
python agent-output/test_claude_code_sdk.py
```

This will test:
- Basic query functionality
- Model selection (sonnet, haiku, opus)
- System prompt support
- Unsupported parameters (temperature, max_tokens, etc.)
- Streaming behavior and chunk sizes
- Max turns limitation
- Working directory (cwd) parameter

### 2. Manual Streaming Analysis

Test streaming performance and chunk sizes:

```python
import asyncio
import time
from claude_code_sdk import query, ClaudeCodeOptions

async def test_streaming():
    start = time.time()
    chunks = []
    
    async for message in query("Write a detailed 5-paragraph essay about AI"):
        chunk_time = time.time() - start
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    chunks.append((chunk_time, len(block.text)))
                    print(f"Chunk at {chunk_time:.2f}s: {len(block.text)} chars")
    
    print(f"\nTotal chunks: {len(chunks)}")
    print(f"Average chunk size: {sum(c[1] for c in chunks) / len(chunks):.0f} chars")

asyncio.run(test_streaming())
```

### 3. Parameter Rejection Test

Verify which parameters cause errors vs silent ignoring:

```python
import asyncio
from claude_code_sdk import ClaudeCodeOptions

# Test each parameter individually
test_params = [
    ('temperature', 0.5),
    ('max_tokens', 100),
    ('top_p', 0.9),
    ('stop_sequences', ['STOP']),
    ('tools', [{'name': 'test', 'description': 'test'}]),
    ('response_format', {'type': 'json_object'})
]

for param_name, param_value in test_params:
    try:
        options = ClaudeCodeOptions(**{param_name: param_value})
        print(f"✅ {param_name}: Accepted (but may be ignored)")
    except TypeError:
        print(f"❌ {param_name}: Rejected by ClaudeCodeOptions")
    except Exception as e:
        print(f"⚠️  {param_name}: Error - {e}")
```

### 4. Compare with LiteLLM Provider

Test our provider implementation:

```bash
# Start LiteLLM server
docker-compose up -d

# Test basic query
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234" \
  -d '{
    "model": "sonnet",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'

# Test streaming
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234" \
  -d '{
    "model": "sonnet",
    "messages": [{"role": "user", "content": "Count to 10"}],
    "stream": true
  }'

# Test with unsupported parameters
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234" \
  -d '{
    "model": "sonnet",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.5,
    "max_tokens": 50
  }'
```

### 5. System Message Handling Test

Verify system message conversion:

```python
# Test current implementation
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"}
]

# Current: converts to "System: You are a helpful assistant\n\nHuman: Hello"
# Proposed: Use ClaudeCodeOptions(system_prompt="You are a helpful assistant")
```

## Expected Results

### ✅ Should Work
- Basic queries
- Model selection
- System prompts (via system_prompt option)
- Streaming (with large chunks)
- OAuth authentication

### ❌ Should NOT Work
- Temperature control
- Max tokens limit
- Stop sequences
- Tool/function calling
- Vision/image input
- Token usage reporting

### ⚠️  Unknown/Partial
- allowed_tools parameter
- permission_mode parameter
- Smooth streaming (SDK limitation)

## Validation Criteria

1. **Pass**: Feature works as expected
2. **Fail**: Feature throws error or doesn't work
3. **Ignored**: Parameter accepted but has no effect
4. **Partial**: Feature works but with limitations

## Results Analysis

After running tests:

1. Check `agent-output/claude_code_sdk_test_results.json` for detailed results
2. Compare actual behavior with expected results
3. Update implementation based on findings
4. Document any surprising discoveries

## Next Steps

Based on test results:

1. **If system_prompt works**: Update provider to use it
2. **If parameters are ignored**: Document this clearly
3. **If streaming is chunky**: Remove manual splitting workaround
4. **If models work**: Ensure all models are properly mapped

## Troubleshooting

### Authentication Issues
```bash
# Re-authenticate
claude-code logout
claude-code login
```

### SDK Not Found
```bash
# Reinstall
pip uninstall claude-code-sdk
pip install claude-code-sdk
```

### Node.js Issues
```bash
# Ensure Node.js is installed
node --version
npm --version
```