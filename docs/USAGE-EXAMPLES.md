# Using LiteLLM-Claude as an OpenAI API

This integration provides an OpenAI-compatible API that translates requests to Claude Agent SDK. Here's how to use it:

## Python with OpenAI Client

```python
from openai import OpenAI

# Point to your local LiteLLM instance
client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-your-desired-custom-key"  # Your LiteLLM master key
)

# Use it exactly like OpenAI
response = client.chat.completions.create(
    model="sonnet",  # or "opus", "haiku"
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)

print(response.choices[0].message.content)
```

## With LangChain

```python
from langchain_openai import ChatOpenAI

# Configure to use your local endpoint
llm = ChatOpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-your-desired-custom-key",
    model="sonnet"
)

response = llm.invoke("What is the meaning of life?")
print(response.content)
```

## With Graphiti

Since Graphiti expects an OpenAI-compatible endpoint, you can configure it like this:

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client import OpenAIClient

# Create an OpenAI client pointing to LiteLLM
llm_client = OpenAIClient(
    base_url="http://localhost:4000/v1",
    api_key="sk-your-desired-custom-key",
    model="sonnet"  # Use Claude Sonnet
)

# Initialize Graphiti with your client
graphiti = Graphiti(
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="password",
    llm_client=llm_client
)
```

## Direct API Calls (cURL)

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-desired-custom-key" \
  -d '{
    "model": "sonnet",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain quantum computing"}
    ],
    "temperature": 0.7
  }'
```

> **Note:** The `temperature` parameter in this example is silently dropped due to `drop_params: true` in `litellm_config.yaml`. See [Parameter Handling](#parameter-handling) below.

## JavaScript/TypeScript

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'http://localhost:4000/v1',
  apiKey: 'sk-your-desired-custom-key',
});

async function main() {
  const completion = await openai.chat.completions.create({
    model: "opus",
    messages: [{ role: "user", content: "Write a haiku about coding" }],
  });

  console.log(completion.choices[0].message.content);
}

main();
```

## Key Points

1. **Base URL**: Always use `http://localhost:4000/v1` (include the `/v1`)
2. **API Key**: Use your LITELLM_MASTER_KEY from the .env file
3. **Models**: See [Available Models](../README.md#available-models) for the complete list

4. **Features Supported**:
   - Chat completions (`/v1/chat/completions`)
   - Model listing (`/v1/models`)
   - Streaming responses (`"stream": true`)

5. **Features NOT Supported**:
   - Embeddings
   - OpenAI-specific parameters (see [Parameter Handling](#parameter-handling) below)

## Parameter Handling

Because LiteLLM is configured with `drop_params: true` and the Claude Agent SDK manages its own parameters, most OpenAI-specific parameters are silently dropped.

### Parameters that work

| Parameter | Description |
|-----------|-------------|
| `model` | Model selection (`sonnet`, `opus`, `haiku`) |
| `messages` | Conversation messages array |
| `stream` | Enable streaming responses (`true`/`false`) |

### Parameters silently dropped

The following parameters are accepted without error but have **no effect**:

| Parameter | Why |
|-----------|-----|
| `temperature` | Claude Agent SDK manages sampling internally |
| `top_p` | Claude Agent SDK manages sampling internally |
| `max_tokens` | Claude Agent SDK manages output length internally |
| `frequency_penalty` | Not supported by Claude Agent SDK |
| `presence_penalty` | Not supported by Claude Agent SDK |
| `stop` | Not supported by Claude Agent SDK |
| `tools` / `tool_choice` | Not supported through this provider |

This is configured via `drop_params: true` in `config/litellm_config.yaml`. Without this setting, unsupported parameters would cause errors.


## Environment Variables for Your App

Instead of hardcoding URLs, use environment variables:

```bash
# .env file
OPENAI_API_BASE=http://localhost:4000/v1
OPENAI_API_KEY=sk-your-desired-custom-key
OPENAI_MODEL=sonnet
```

Then in your code:
```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY")
)

model = os.getenv("OPENAI_MODEL", "sonnet")
```

This way, you can easily switch between real OpenAI and your LiteLLM-Claude instance by changing environment variables.