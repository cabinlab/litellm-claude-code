# Definitive Claude Code SDK Streaming Findings

## Source Code Evidence

### 1. Hardcoded Output Format
**File**: `src/claude_code_sdk/_internal/transport/subprocess_cli.py`
**Line**: 73
```python
def _build_command(self) -> list[str]:
    """Build CLI command with arguments."""
    cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]
```
**Finding**: Output format is hardcoded. No way to change it.

### 2. Message Reception
**File**: `src/claude_code_sdk/_internal/transport/subprocess_cli.py`
**Lines**: 175-185
```python
async for line in self._stdout_stream:
    line_str = line.strip()
    if not line_str:
        continue
    
    try:
        data = json.loads(line_str)  # Each line is complete JSON
        yield data
```
**Finding**: SDK reads stdout line by line, parsing each as complete JSON.

### 3. Message Parsing
**File**: `src/claude_code_sdk/_internal/client.py`
**Lines**: 44-71
```python
case "assistant":
    content_blocks: list[ContentBlock] = []
    for block in data["message"]["content"]:
        match block["type"]:
            case "text":
                content_blocks.append(TextBlock(text=block["text"]))
```
**Finding**: Assistant messages contain complete `TextBlock` objects with full text, not deltas.

### 4. Single Transport Implementation
**File**: `src/claude_code_sdk/_internal/client.py`
**Line**: 31
```python
transport = SubprocessCLITransport(prompt=prompt, options=options)
```
**Finding**: Only one transport exists. No alternatives.

### 5. No Streaming Configuration
**File**: `src/claude_code_sdk/types.py`
**ClaudeCodeOptions class**
```python
@dataclass
class ClaudeCodeOptions:
    """Query options for Claude SDK."""
    
    allowed_tools: list[str] = field(default_factory=list)
    max_thinking_tokens: int = 8000
    system_prompt: str | None = None
    # ... other fields
    # NO output_format or streaming options
```
**Finding**: No parameters to control output format or streaming behavior.

## Message Flow

1. **CLI Command**: `claude --output-format stream-json --verbose --print "prompt"`
2. **CLI Output**: Newline-delimited JSON (NDJSON)
3. **SDK Parsing**: Each line → Complete JSON object → Complete Message
4. **User Receives**: Full messages, not incremental updates

## Example JSON Stream

```json
{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Here is my complete response to your question."}]}}
{"type": "result", "subtype": "success", "duration_ms": 1500, "total_cost_usd": 0.002, "session_id": "abc123"}
```

## Definitive Conclusion

**The Claude Code SDK provides message-level streaming, not token-level streaming.**

- **What exists**: Complete messages streamed as they're generated
- **What doesn't**: Character-by-character or token-by-token updates
- **Why**: Architectural decision - SDK wraps CLI that outputs complete JSON messages
- **Can it be changed**: No, without modifying SDK source code

This is not a bug or limitation to be fixed - it's the intended design for a tool focused on code operations rather than real-time conversational streaming.