# Claude SDK Streaming Evolution

## Executive Summary

The introduction of ClaudeSDKClient in version 0.0.16 (July 2025) represents a **fundamental architectural shift** in how Claude Code handles streaming, moving from a **unidirectional, message-based approach** to a **truly bidirectional, interactive streaming model**. While both approaches use JSON streaming over subprocess pipes, the key difference lies in the communication protocol and interaction capabilities.

## The Evolution: From query() to ClaudeSDKClient

### Before ClaudeSDKClient: The query() Function

The original `query()` function provided a **unidirectional streaming interface**:

```python
# Original query() approach
async for message in query("What is 2+2?", options=options):
    # Process messages as they arrive
    if isinstance(message, AssistantMessage):
        print(message.content)
```

**Key Characteristics:**
- **One-shot execution**: Each query spawns a new subprocess
- **Unidirectional flow**: Send prompt → Receive stream of messages → Process terminates
- **Message-based streaming**: Messages arrive as complete JSON objects via stdout
- **No session persistence**: Each query is independent
- **No interrupt capability**: Once started, must run to completion

### After ClaudeSDKClient: True Bidirectional Streaming

The ClaudeSDKClient introduces **persistent, bidirectional streaming**:

```python
# New ClaudeSDKClient approach
async with ClaudeSDKClient() as client:
    # Persistent connection maintained
    await client.query("What is 2+2?")
    async for message in client.receive_response():
        process_message(message)
    
    # Can send follow-up without reconnecting
    await client.query("Multiply that by 10")
    async for message in client.receive_response():
        process_message(message)
```

**Key Characteristics:**
- **Persistent subprocess**: One long-running CLI process
- **Bidirectional communication**: Can send new messages while receiving responses
- **True streaming protocol**: Uses `--input-format stream-json` and `--output-format stream-json`
- **Session management**: Maintains conversation context
- **Interrupt support**: Can interrupt mid-stream with control messages

## Technical Deep Dive: What Actually Changed?

### 1. Transport Layer Evolution

**Before (query function):**
```python
# Simplified internal implementation
async def query(prompt: str, options: ClaudeCodeOptions):
    # Spawn new subprocess for each query
    cmd = ["claude", "--output-format", "stream-json", "--print", prompt]
    process = await anyio.open_process(cmd)
    
    # Read messages from stdout until process terminates
    async for line in process.stdout:
        message = json.loads(line)
        yield parse_message(message)
```

**After (ClaudeSDKClient):**
```python
# Persistent subprocess with bidirectional pipes
class SubprocessCLITransport:
    async def connect(self):
        # Spawn with bidirectional streaming enabled
        cmd = ["claude", 
               "--output-format", "stream-json",
               "--input-format", "stream-json"]  # Key difference!
        
        self.process = await anyio.open_process(cmd, stdin=PIPE, stdout=PIPE)
        self.stdin = TextSendStream(self.process.stdin)
        self.stdout = TextReceiveStream(self.process.stdout)
```

### 2. Message Protocol Changes

**Before:** Messages flowed in one direction only
```
Python SDK → CLI (via command line args) → Claude API → CLI → Python SDK (via stdout)
```

**After:** Full duplex communication
```
Python SDK ←→ CLI (via stdin/stdout pipes) ←→ Claude API
```

### 3. Streaming Granularity

**Important Finding:** Both approaches stream at the **message level**, not the token level. The "streaming" refers to:

- **Before**: Streaming complete messages (assistant responses, tool uses, results) as they become available
- **After**: Same message-level streaming, but with the ability to send new messages during reception

Neither approach provides true **token-by-token streaming** like you might see in a web interface. Messages arrive as complete JSON objects:

```json
{
  "type": "assistant",
  "message": {
    "content": [
      {"type": "text", "text": "The answer is 4."}
    ]
  }
}
```

### 4. Control Flow Capabilities

**Before (query):**
- Fire and forget
- No ability to modify or interrupt
- Sequential execution only

**After (ClaudeSDKClient):**
- Interactive control flow
- Interrupt capability via control messages:
  ```json
  {
    "type": "control_request",
    "request": {"subtype": "interrupt"}
  }
  ```
- Concurrent send/receive operations

## Key Insights: What "Streaming" Really Means

### It's NOT Token Streaming

Despite the name "streaming," neither implementation provides character-by-character or token-by-token streaming. The streaming refers to:

1. **Incremental message delivery**: Messages arrive as they're generated, not all at once
2. **Asynchronous processing**: Can process messages while Claude continues working
3. **Tool execution feedback**: See tool results as they complete

### It IS Bidirectional Communication

The revolutionary aspect of ClaudeSDKClient is the **bidirectional** nature:

1. **Persistent connection**: Maintains state across multiple interactions
2. **Concurrent operations**: Send new prompts while processing responses
3. **Dynamic interaction**: React to Claude's responses in real-time
4. **Session continuity**: Conversation context preserved

## Practical Implications

### Performance Impact

**query() function:**
- 2-3 second startup overhead per query
- Process spawn/teardown cost
- No connection reuse

**ClaudeSDKClient:**
- One-time connection cost
- Amortized over entire session
- Efficient for interactive use cases

### Use Case Alignment

**When query() is still appropriate:**
- One-off operations
- Batch processing with independent prompts
- Simple automation scripts
- Stateless operations

**When ClaudeSDKClient shines:**
- Interactive applications
- Chat interfaces
- Multi-turn conversations
- Real-time collaboration tools
- Applications requiring interrupt capability

## Code Examples: The Difference in Practice

### Example 1: Simple Query

**Before (query):**
```python
async def get_answer(prompt: str):
    messages = []
    async for msg in query(prompt):
        messages.append(msg)
    return messages
```

**After (ClaudeSDKClient):**
```python
async def get_answer(prompt: str):
    async with ClaudeSDKClient() as client:
        await client.query(prompt)
        messages = []
        async for msg in client.receive_response():
            messages.append(msg)
        return messages
```

### Example 2: Interactive Conversation

**Before (query) - Not Possible**
```python
# Each query is independent - no conversation context
async for msg in query("Remember the number 42"):
    pass

# This won't remember the previous interaction
async for msg in query("What number did I mention?"):
    pass  # Claude has no context
```

**After (ClaudeSDKClient) - Natural Conversation**
```python
async with ClaudeSDKClient() as client:
    await client.query("Remember the number 42")
    async for msg in client.receive_response():
        pass
    
    # This maintains context
    await client.query("What number did I mention?")
    async for msg in client.receive_response():
        pass  # Claude responds: "You mentioned the number 42"
```

### Example 3: Interrupt Handling

**Before (query) - Not Supported**
```python
# No way to interrupt once started
async for msg in query("Count to 1000000"):
    # Must wait for completion
    pass
```

**After (ClaudeSDKClient) - Full Control**
```python
async with ClaudeSDKClient() as client:
    await client.query("Count to 1000000")
    
    # Can interrupt mid-stream
    interrupt_task = asyncio.create_task(
        interrupt_after_delay(client, 2.0)
    )
    
    async for msg in client.receive_messages():
        if should_stop(msg):
            await client.interrupt()
            break
```

## Conclusion

The evolution from `query()` to `ClaudeSDKClient` represents a shift from a **simple request-response streaming model** to a **full bidirectional communication protocol**. While both use JSON message streaming over subprocess pipes, the ClaudeSDKClient introduces:

1. **Persistent connections** instead of one-shot processes
2. **Bidirectional communication** via stdin/stdout pipes
3. **Session management** with conversation context
4. **Interrupt capabilities** for dynamic control
5. **Concurrent send/receive** operations

The term "streaming" in both cases refers to **incremental message delivery**, not token-level streaming. The real innovation is the move from unidirectional message streams to truly interactive, bidirectional communication channels.

This architectural change enables building sophisticated interactive applications, chat interfaces, and multi-agent systems that were not possible with the original query() function approach.