# ClaudeSDKClient Usage Patterns

This guide provides practical, runnable code examples and best practices for using the ClaudeSDKClient feature in the Claude Code Python SDK. All examples are based on official Anthropic code patterns.

## Table of Contents

1. [Basic Usage Patterns](#basic-usage-patterns)
2. [Advanced Streaming Patterns](#advanced-streaming-patterns)
3. [Error Handling Strategies](#error-handling-strategies)
4. [Integration with Python Frameworks](#integration-with-python-frameworks)
5. [Performance Tips](#performance-tips)
6. [Migration from query() to ClaudeSDKClient](#migration-from-query-to-claudesdkclient)
7. [Best Practices and Anti-Patterns](#best-practices-and-anti-patterns)

## Basic Usage Patterns

### Simple Interactive Conversation

The most straightforward way to use ClaudeSDKClient is with a context manager:

```python
from claude_code_sdk import ClaudeSDKClient

async def basic_conversation():
    async with ClaudeSDKClient() as client:
        # Send a message
        await client.query("What is the capital of France?")
        
        # Receive complete response
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
```

### Multi-Turn Conversations

ClaudeSDKClient maintains conversation context across multiple exchanges:

```python
from claude_code_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def multi_turn_conversation():
    async with ClaudeSDKClient() as client:
        # First turn
        await client.query("What's the capital of France?")
        
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                print_assistant_message(msg)
        
        # Second turn - Claude remembers context
        await client.query("What's the population of that city?")
        
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                print_assistant_message(msg)

def print_assistant_message(msg):
    """Helper to extract text from assistant messages."""
    for block in msg.content:
        if isinstance(block, TextBlock):
            print(f"Claude: {block.text}")
```

### Session Management

Use session IDs to maintain separate conversation contexts:

```python
async def multiple_sessions():
    async with ClaudeSDKClient() as client:
        # Math conversation
        await client.query("What's 2+2?", session_id="math-session")
        async for msg in client.receive_response():
            process_message(msg)
        
        # History conversation (separate context)
        await client.query("Who was Napoleon?", session_id="history-session")
        async for msg in client.receive_response():
            process_message(msg)
        
        # Back to math - maintains context
        await client.query("Multiply that by 10", session_id="math-session")
        async for msg in client.receive_response():
            process_message(msg)
```

## Advanced Streaming Patterns

### Concurrent Send and Receive

Process responses while sending new messages:

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, AssistantMessage, ResultMessage

async def concurrent_interaction():
    async with ClaudeSDKClient() as client:
        # Background task to continuously receive messages
        async def receive_messages():
            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    print(f"Received: {extract_text(message)[:50]}...")
                elif isinstance(message, ResultMessage):
                    print(f"Completed query (cost: ${message.total_cost_usd:.4f})")
        
        # Start receiving in background
        receive_task = asyncio.create_task(receive_messages())
        
        # Send multiple queries
        questions = [
            "What is 2 + 2?",
            "What is the square root of 144?",
            "What is 10% of 80?"
        ]
        
        for question in questions:
            await client.query(question)
            await asyncio.sleep(2)  # Space out requests
        
        # Wait for responses
        await asyncio.sleep(3)
        
        # Clean up
        receive_task.cancel()
        await asyncio.shield(receive_task)
```

### Interrupt Handling

Interrupt long-running tasks with proper message consumption:

```python
async def interrupt_example():
    async with ClaudeSDKClient() as client:
        # Start a long task
        await client.query("Count from 1 to 1000 slowly")
        
        # IMPORTANT: Must consume messages for interrupt to work
        interrupt_sent = False
        
        async def consume_messages():
            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    text = extract_text(message)
                    print(f"Claude: {text[:30]}...")
                    
                    # Check if we should interrupt
                    if "50" in text and not interrupt_sent:
                        return True  # Signal to interrupt
                elif isinstance(message, ResultMessage):
                    return False  # Normal completion
        
        # Start consuming
        should_interrupt = await consume_messages()
        
        if should_interrupt:
            print("\n[Interrupting...]")
            await client.interrupt()
            
            # Send new instruction
            await client.query("Never mind, just give me a summary of what you were doing")
            
            async for msg in client.receive_response():
                print_assistant_message(msg)
```

### Async Iterable Prompts

Send multiple messages as a stream:

```python
async def streaming_prompts():
    async def create_message_stream():
        """Generate a stream of user messages."""
        questions = [
            "What's the weather like?",
            "What should I wear today?",
            "Any restaurant recommendations?"
        ]
        
        for question in questions:
            yield {
                "type": "user",
                "message": {"role": "user", "content": question},
                "parent_tool_use_id": None,
                "session_id": "planning-session"
            }
            # Small delay between messages
            await asyncio.sleep(0.5)
    
    async with ClaudeSDKClient() as client:
        # Send the message stream
        await client.query(create_message_stream())
        
        # Process all responses
        response_count = 0
        async for msg in client.receive_messages():
            if isinstance(msg, ResultMessage):
                response_count += 1
                if response_count >= 3:  # Got all three responses
                    break
            else:
                process_message(msg)
```

## Error Handling Strategies

### Basic Error Handling

```python
from claude_code_sdk import ClaudeSDKClient, CLIConnectionError, ProcessError
import asyncio

async def robust_conversation():
    client = ClaudeSDKClient()
    
    try:
        await client.connect()
        
        # Send query with timeout
        await client.query("Analyze this complex problem...")
        
        # Receive with timeout
        try:
            async with asyncio.timeout(30.0):  # 30 second timeout
                async for msg in client.receive_response():
                    process_message(msg)
        except asyncio.TimeoutError:
            print("Response timeout - Claude is taking too long")
            # Optionally interrupt
            await client.interrupt()
            
    except CLIConnectionError as e:
        print(f"Connection failed: {e}")
        # Handle connection issues
        
    except ProcessError as e:
        print(f"Process error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
            
    finally:
        # Always disconnect
        await client.disconnect()
```

### Retry Logic with Exponential Backoff

```python
import asyncio
from typing import TypeVar, Callable
from claude_code_sdk import ClaudeSDKClient, CLIConnectionError

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> T:
    """Retry a function with exponential backoff."""
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return await func()
        except CLIConnectionError as e:
            if attempt == max_retries - 1:
                raise
            
            print(f"Attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {delay:.1f} seconds...")
            await asyncio.sleep(delay)
            delay *= backoff_factor

async def reliable_query(prompt: str):
    """Query with automatic retry on connection errors."""
    async def _query():
        async with ClaudeSDKClient() as client:
            await client.query(prompt)
            
            responses = []
            async for msg in client.receive_response():
                responses.append(msg)
            return responses
    
    return await retry_with_backoff(_query)
```

### Graceful Degradation

```python
async def graceful_conversation():
    """Fallback to simpler queries if complex ones fail."""
    async with ClaudeSDKClient() as client:
        try:
            # Try complex query with tools
            options = ClaudeCodeOptions(
                allowed_tools=["Read", "Write", "Bash"],
                max_thinking_tokens=20000
            )
            await client.query(
                "Analyze the codebase and create a comprehensive report",
                session_id="analysis"
            )
            
        except (CLIConnectionError, ProcessError) as e:
            print(f"Complex query failed: {e}")
            print("Falling back to simpler query...")
            
            # Retry with minimal configuration
            simple_client = ClaudeSDKClient(
                ClaudeCodeOptions(allowed_tools=[], max_thinking_tokens=5000)
            )
            async with simple_client as client:
                await client.query("Provide a high-level code overview")
                async for msg in client.receive_response():
                    process_message(msg)
```

## Integration with Python Frameworks

### FastAPI Integration

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from claude_code_sdk import ClaudeSDKClient, AssistantMessage, TextBlock
import asyncio
import json

app = FastAPI()

# Singleton client for the application
claude_client = None

@app.on_event("startup")
async def startup_event():
    global claude_client
    claude_client = ClaudeSDKClient()
    await claude_client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    if claude_client:
        await claude_client.disconnect()

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            prompt = data.get("prompt")
            session_id = data.get("session_id", "default")
            
            # Send to Claude
            await claude_client.query(prompt, session_id=session_id)
            
            # Stream responses back
            async for msg in claude_client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            await websocket.send_json({
                                "type": "message",
                                "content": block.text
                            })
                elif isinstance(msg, ResultMessage):
                    await websocket.send_json({
                        "type": "complete",
                        "cost": msg.total_cost_usd
                    })
                    
    except WebSocketDisconnect:
        print(f"Client disconnected")

@app.get("/stream-query/{prompt}")
async def stream_query(prompt: str):
    """HTTP streaming endpoint."""
    async def generate():
        await claude_client.query(prompt)
        
        async for msg in claude_client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        yield f"data: {json.dumps({'text': block.text})}\n\n"
            elif isinstance(msg, ResultMessage):
                yield f"data: {json.dumps({'done': True, 'cost': msg.total_cost_usd})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Django Channels Integration

```python
# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from claude_code_sdk import ClaudeSDKClient, AssistantMessage, TextBlock
from django.core.cache import cache

class ClaudeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.client = ClaudeSDKClient()
        
        await self.accept()
        await self.client.connect()
        
        # Store client in cache for session persistence
        cache.set(f"claude_client_{self.session_id}", self.client, 3600)
    
    async def disconnect(self, close_code):
        if hasattr(self, 'client'):
            await self.client.disconnect()
        cache.delete(f"claude_client_{self.session_id}")
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'query':
            await self.handle_query(data['content'])
        elif message_type == 'interrupt':
            await self.client.interrupt()
    
    async def handle_query(self, prompt):
        await self.client.query(prompt, session_id=self.session_id)
        
        async for msg in self.client.receive_response():
            if isinstance(msg, AssistantMessage):
                await self.send(text_data=json.dumps({
                    'type': 'assistant_message',
                    'content': self.extract_text(msg)
                }))
            elif isinstance(msg, ResultMessage):
                await self.send(text_data=json.dumps({
                    'type': 'complete',
                    'stats': {
                        'duration_ms': msg.duration_ms,
                        'cost_usd': msg.total_cost_usd,
                        'turns': msg.num_turns
                    }
                }))
    
    def extract_text(self, msg):
        texts = []
        for block in msg.content:
            if isinstance(block, TextBlock):
                texts.append(block.text)
        return '\n'.join(texts)
```

### Async Context Manager Pattern

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
from claude_code_sdk import ClaudeSDKClient, Message

class ClaudeConversation:
    """High-level wrapper for conversational patterns."""
    
    def __init__(self, options=None):
        self.client = ClaudeSDKClient(options)
        self.history = []
    
    async def __aenter__(self):
        await self.client.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()
    
    async def ask(self, prompt: str) -> str:
        """Send a query and return the complete response as text."""
        await self.client.query(prompt)
        
        response_parts = []
        async for msg in self.client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
        
        response = '\n'.join(response_parts)
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": response})
        
        return response
    
    async def ask_stream(self, prompt: str) -> AsyncIterator[str]:
        """Send a query and yield response chunks as they arrive."""
        await self.client.query(prompt)
        
        async for msg in self.client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        yield block.text

# Usage
async def main():
    async with ClaudeConversation() as conv:
        # Simple ask
        answer = await conv.ask("What's the capital of France?")
        print(answer)
        
        # Streaming ask
        print("\nStreaming response:")
        async for chunk in conv.ask_stream("Tell me about that city"):
            print(chunk, end='', flush=True)
```

## Performance Tips

### 1. Connection Reuse

Maintain a single client connection for multiple queries:

```python
# Good: Reuse connection
async def process_multiple_queries(queries: list[str]):
    async with ClaudeSDKClient() as client:
        for query in queries:
            await client.query(query)
            async for msg in client.receive_response():
                process_message(msg)

# Bad: Create new connection for each query
async def inefficient_queries(queries: list[str]):
    for query in queries:
        async with ClaudeSDKClient() as client:  # New connection each time!
            await client.query(query)
            async for msg in client.receive_response():
                process_message(msg)
```

### 2. Concurrent Processing

Process multiple sessions concurrently:

```python
async def concurrent_sessions(user_queries: dict[str, list[str]]):
    """Process queries from multiple users concurrently."""
    async def process_user_session(user_id: str, queries: list[str]):
        async with ClaudeSDKClient() as client:
            for query in queries:
                await client.query(query, session_id=user_id)
                async for msg in client.receive_response():
                    store_response(user_id, msg)
    
    # Process all users concurrently
    tasks = [
        process_user_session(user_id, queries)
        for user_id, queries in user_queries.items()
    ]
    await asyncio.gather(*tasks)
```

### 3. Message Buffering

Implement buffering for high-throughput scenarios:

```python
from collections import deque
import asyncio

class BufferedClaudeClient:
    def __init__(self, max_buffer_size=100):
        self.client = ClaudeSDKClient()
        self.message_buffer = deque(maxlen=max_buffer_size)
        self.processing = False
    
    async def __aenter__(self):
        await self.client.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()
    
    async def buffered_query(self, prompt: str, session_id: str = "default"):
        """Add query to buffer and process asynchronously."""
        self.message_buffer.append((prompt, session_id))
        
        if not self.processing:
            asyncio.create_task(self._process_buffer())
    
    async def _process_buffer(self):
        """Process buffered messages in batches."""
        self.processing = True
        
        while self.message_buffer:
            prompt, session_id = self.message_buffer.popleft()
            
            try:
                await self.client.query(prompt, session_id=session_id)
                
                # Process response without blocking
                asyncio.create_task(self._consume_response(session_id))
                
            except Exception as e:
                print(f"Error processing {prompt}: {e}")
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.1)
        
        self.processing = False
    
    async def _consume_response(self, session_id: str):
        """Consume response in background."""
        async for msg in self.client.receive_response():
            # Store or process message asynchronously
            await self.handle_message(msg, session_id)
    
    async def handle_message(self, msg, session_id: str):
        """Override this to handle messages."""
        pass
```

### 4. Memory-Efficient Streaming

Process large responses without loading everything into memory:

```python
async def process_large_response(client: ClaudeSDKClient, prompt: str):
    """Process response in chunks to minimize memory usage."""
    await client.query(prompt)
    
    # Process and immediately write to file
    with open("response.txt", "w") as f:
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        # Write immediately, don't accumulate
                        f.write(block.text)
                        f.flush()  # Ensure it's written
    
    print("Response saved to response.txt")
```

## Migration from query() to ClaudeSDKClient

### Simple Migration

Before (using query):
```python
from claude_code_sdk import query

# One-shot query
async def old_way():
    messages = []
    async for msg in query("What is 2+2?"):
        messages.append(msg)
    return messages
```

After (using ClaudeSDKClient):
```python
from claude_code_sdk import ClaudeSDKClient

# Equivalent with ClaudeSDKClient
async def new_way():
    async with ClaudeSDKClient() as client:
        await client.query("What is 2+2?")
        
        messages = []
        async for msg in client.receive_response():
            messages.append(msg)
        return messages
```

### Migration with Options

Before:
```python
from claude_code_sdk import query, ClaudeCodeOptions

options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write"],
    system_prompt="You are a helpful assistant"
)

async for msg in query("Create a hello.txt file", options=options):
    process_message(msg)
```

After:
```python
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write"],
    system_prompt="You are a helpful assistant"
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Create a hello.txt file")
    async for msg in client.receive_response():
        process_message(msg)
```

### When to Keep Using query()

The `query()` function is still appropriate for:

1. **Simple one-off queries**:
```python
# Good use of query()
async def get_quick_answer(prompt: str):
    async for msg in query(prompt):
        if isinstance(msg, AssistantMessage):
            return extract_text(msg)
```

2. **Batch processing**:
```python
# Good use of query() for independent queries
async def batch_process(prompts: list[str]):
    results = []
    for prompt in prompts:
        response = []
        async for msg in query(prompt):
            response.append(msg)
        results.append(response)
    return results
```

3. **Fire-and-forget operations**:
```python
# Good use of query()
async def log_event(event: str):
    async for _ in query(f"Log this event: {event}"):
        pass  # Just ensure it completes
```

## Best Practices and Anti-Patterns

### Best Practices

1. **Always use context managers**:
```python
# Good
async with ClaudeSDKClient() as client:
    # Your code here
    pass

# Also good for explicit control
client = ClaudeSDKClient()
try:
    await client.connect()
    # Your code here
finally:
    await client.disconnect()
```

2. **Handle all message types**:
```python
async def comprehensive_handler(client: ClaudeSDKClient):
    async for msg in client.receive_messages():
        if isinstance(msg, UserMessage):
            log_user_message(msg)
        elif isinstance(msg, AssistantMessage):
            process_assistant_response(msg)
        elif isinstance(msg, SystemMessage):
            handle_system_event(msg)
        elif isinstance(msg, ResultMessage):
            record_completion_stats(msg)
            break  # Result indicates completion
```

3. **Use type hints and validation**:
```python
from typing import AsyncIterator
from claude_code_sdk import Message, AssistantMessage, TextBlock

async def get_text_response(
    client: ClaudeSDKClient,
    prompt: str
) -> AsyncIterator[str]:
    """Yield only text content from assistant messages."""
    await client.query(prompt)
    
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    yield block.text
```

4. **Implement proper cleanup**:
```python
import signal
import asyncio

class GracefulClaudeClient:
    def __init__(self):
        self.client = ClaudeSDKClient()
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\nGracefully shutting down...")
        self.running = False
    
    async def run(self):
        await self.client.connect()
        
        try:
            while self.running:
                # Your application logic
                await asyncio.sleep(1)
        finally:
            await self.client.disconnect()
            print("Cleanup complete")
```

### Anti-Patterns to Avoid

1. **Don't forget to consume messages when using interrupt**:
```python
# Bad: Interrupt without message consumption
async def bad_interrupt():
    async with ClaudeSDKClient() as client:
        await client.query("Count to 1000")
        await asyncio.sleep(1)
        await client.interrupt()  # Won't work!

# Good: Consume messages for interrupt to work
async def good_interrupt():
    async with ClaudeSDKClient() as client:
        await client.query("Count to 1000")
        
        # Must consume messages
        consume_task = asyncio.create_task(
            consume_until_interrupted(client)
        )
        
        await asyncio.sleep(1)
        await client.interrupt()
        await consume_task
```

2. **Don't create multiple clients for the same conversation**:
```python
# Bad: Multiple clients lose context
async def bad_conversation():
    # First message
    async with ClaudeSDKClient() as client:
        await client.query("Remember the number 42")
        async for msg in client.receive_response():
            pass
    
    # Second message - no context!
    async with ClaudeSDKClient() as client:
        await client.query("What number did I mention?")
        # Claude won't remember!

# Good: Single client maintains context
async def good_conversation():
    async with ClaudeSDKClient() as client:
        await client.query("Remember the number 42")
        async for msg in client.receive_response():
            pass
        
        await client.query("What number did I mention?")
        # Claude remembers: 42
```

3. **Don't block the event loop**:
```python
# Bad: Blocking operation
async def bad_processing(client: ClaudeSDKClient):
    await client.query("Generate some data")
    
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            # Bad: Blocking CPU-intensive operation
            result = expensive_sync_computation(msg)
            save_to_database_sync(result)

# Good: Use thread pool for blocking operations
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def good_processing(client: ClaudeSDKClient):
    await client.query("Generate some data")
    
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            # Run blocking operations in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor, expensive_sync_computation, msg
            )
            await loop.run_in_executor(
                executor, save_to_database_sync, result
            )
```

4. **Don't ignore error states**:
```python
# Bad: Ignoring errors
async def bad_error_handling():
    async with ClaudeSDKClient() as client:
        await client.query("Do something")
        async for msg in client.receive_response():
            # What if msg is an error?
            print(msg)

# Good: Check result messages
async def good_error_handling():
    async with ClaudeSDKClient() as client:
        await client.query("Do something")
        
        async for msg in client.receive_response():
            if isinstance(msg, ResultMessage):
                if msg.is_error:
                    print(f"Error occurred: {msg.subtype}")
                    # Handle error appropriately
                else:
                    print(f"Success! Cost: ${msg.total_cost_usd:.4f}")
            else:
                process_message(msg)
```

## Conclusion

The ClaudeSDKClient provides a powerful interface for building interactive AI applications. By following these patterns and best practices, you can create robust, efficient, and maintainable applications that leverage Claude's capabilities effectively.

Remember:
- Use ClaudeSDKClient for interactive, stateful conversations
- Keep query() for simple, one-off operations
- Always handle errors and edge cases
- Consume messages when using interrupts
- Leverage async patterns for optimal performance

For more examples, see the official Anthropic examples at:
- [streaming_mode.py](https://github.com/anthropics/claude-code-sdk-python/blob/main/examples/streaming_mode.py)
- [streaming_mode_trio.py](https://github.com/anthropics/claude-code-sdk-python/blob/main/examples/streaming_mode_trio.py)