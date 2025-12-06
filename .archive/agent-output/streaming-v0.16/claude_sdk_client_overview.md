# ClaudeSDKClient: Bidirectional Streaming Conversation Overview

## Summary

The `ClaudeSDKClient` is a new feature introduced in version 0.0.16 of the Claude Code Python SDK that enables **bidirectional, interactive conversations** with Claude Code. Unlike the simpler `query()` function that handles one-shot or unidirectional interactions, `ClaudeSDKClient` provides full control over conversation flow with support for streaming, interrupts, and dynamic message sending.

## What is "Bidirectional Streaming Conversation"?

In this context, "bidirectional streaming conversation" means:

1. **Bidirectional**: You can both send messages TO Claude and receive messages FROM Claude at any time during the conversation
2. **Streaming**: Messages are processed as streams - you can send follow-up messages while still receiving responses from previous queries
3. **Stateful**: The conversation maintains context across multiple message exchanges
4. **Interactive**: You can react to Claude's responses and send new messages based on what Claude says
5. **Interruptible**: You can interrupt Claude mid-response and send new instructions

## Key Features

- **Full conversation control**: Send and receive messages at any time
- **Interrupt support**: Can interrupt Claude's responses with new instructions
- **Session management**: Maintains conversation state across messages
- **Flexible message sending**: Support for both string prompts and async iterables
- **Context manager support**: Automatic connection/disconnection with `async with`
- **Real-time interaction**: Ideal for chat interfaces and interactive applications

## Implementation Details

### Source File Location
- **Main implementation**: [`src/claude_code_sdk/client.py`](https://github.com/anthropics/claude-code-sdk-python/blob/main/src/claude_code_sdk/client.py)
- **Export location**: [`src/claude_code_sdk/__init__.py`](https://github.com/anthropics/claude-code-sdk-python/blob/main/src/claude_code_sdk/__init__.py)

### Key Code Snippet - ClaudeSDKClient Class Definition

```python
class ClaudeSDKClient:
    """
    Client for bidirectional, interactive conversations with Claude Code.

    This client provides full control over the conversation flow with support
    for streaming, interrupts, and dynamic message sending. For simple one-shot
    queries, consider using the query() function instead.

    Key features:
    - **Bidirectional**: Send and receive messages at any time
    - **Stateful**: Maintains conversation context across messages
    - **Interactive**: Send follow-ups based on responses
    - **Control flow**: Support for interrupts and session management
    """

    def __init__(self, options: ClaudeCodeOptions | None = None):
        """Initialize Claude SDK client."""
        if options is None:
            options = ClaudeCodeOptions()
        self.options = options
        self._transport: Any | None = None
        os.environ["CLAUDE_CODE_ENTRYPOINT"] = "sdk-py-client"

    async def connect(
        self, prompt: str | AsyncIterable[dict[str, Any]] | None = None
    ) -> None:
        """Connect to Claude with a prompt or message stream."""
        # Implementation details...

    async def query(
        self, prompt: str | AsyncIterable[dict[str, Any]], session_id: str = "default"
    ) -> None:
        """Send a new request in streaming mode."""
        # Implementation details...

    async def receive_messages(self) -> AsyncIterator[Message]:
        """Receive all messages from Claude."""
        # Implementation details...

    async def receive_response(self) -> AsyncIterator[Message]:
        """
        Receive messages from Claude until and including a ResultMessage.
        
        This async iterator yields all messages in sequence and automatically terminates
        after yielding a ResultMessage (which indicates the response is complete).
        """
        # Implementation details...

    async def interrupt(self) -> None:
        """Send interrupt signal (only works with streaming mode)."""
        # Implementation details...

    async def disconnect(self) -> None:
        """Disconnect from Claude."""
        # Implementation details...
```

## Usage Examples

### Basic Interactive Conversation

```python
from claude_code_sdk import ClaudeSDKClient

# Automatically connects with empty stream for interactive use
async with ClaudeSDKClient() as client:
    # Send initial message
    await client.query("Let's solve a math problem step by step")
    
    # Receive and process response
    async for message in client.receive_messages():
        if "ready" in str(message.content).lower():
            break
    
    # Send follow-up based on response
    await client.query("What's 15% of 80?")
    
    # Continue conversation...
# Automatically disconnects
```

### With Interrupt Capability

```python
import anyio
from claude_code_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    # Start a long task
    await client.query("Count to 1000")
    
    # Interrupt after 2 seconds
    await anyio.sleep(2)
    await client.interrupt()
    
    # Send new instruction
    await client.query("Never mind, what's 2+2?")
```

### Multi-Turn Conversation

```python
async with ClaudeSDKClient() as client:
    # First turn
    await client.query("What's the capital of France?")
    
    # Extract and print response
    async for msg in client.receive_response():
        display_message(msg)
    
    # Second turn - follow-up
    await client.query("What's the population of that city?")
    
    async for msg in client.receive_response():
        display_message(msg)
```

## When to Use ClaudeSDKClient vs query()

### Use ClaudeSDKClient when:
- Building chat interfaces or conversational UIs
- Interactive debugging or exploration sessions
- Multi-turn conversations with context
- You need to react to Claude's responses
- Real-time applications with user input
- You need interrupt capabilities

### Use query() when:
- Simple one-off questions
- Batch processing of prompts
- Fire-and-forget automation scripts
- All inputs are known upfront
- Stateless operations

## Related Information

- **Introduced in**: PR [#75 "Implement streaming"](https://github.com/anthropics/claude-code-sdk-python/pull/75) by @dicksontsai
- **Released in**: Version 0.0.16 (July 2025)
- **Changelog entry**: "Introduce ClaudeSDKClient for bidirectional streaming conversation"
- **Examples**: See [`examples/streaming_mode.py`](https://github.com/anthropics/claude-code-sdk-python/blob/main/examples/streaming_mode.py) for comprehensive examples
- **Tests**: See [`tests/test_streaming_client.py`](https://github.com/anthropics/claude-code-sdk-python/blob/main/tests/test_streaming_client.py)

## Technical Architecture

The ClaudeSDKClient uses a subprocess-based transport layer to communicate with the Claude Code CLI. It maintains a persistent connection that allows for:

1. **Async message streams**: Both sending and receiving messages asynchronously
2. **Session management**: Each conversation can have a session ID for context
3. **Transport abstraction**: Uses `SubprocessCLITransport` internally to handle CLI communication
4. **Message parsing**: Converts raw CLI output to typed Message objects

The implementation is compatible with multiple async runtimes (asyncio, trio) thanks to the use of `anyio` for async operations.