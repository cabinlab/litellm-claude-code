# Using LiteLLM-Claude as an OpenAI API

This integration provides an OpenAI-compatible API that translates requests to Claude Code SDK. Here's how to use it:

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
    model="sonnet",  # or "opus", "claude-3-5-haiku-20241022", "default"
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
3. **Models**: Use exactly these names:
   - `sonnet` (Claude Sonnet)
   - `opus` (Claude Opus)
   - `claude-3-5-haiku-20241022` (Claude 3.5 Haiku)
   - `default` (Opus with Sonnet fallback)

4. **Features Supported**:
   - Chat completions (`/v1/chat/completions`)
   - Model listing (`/v1/models`)
   - Standard OpenAI parameters (temperature, max_tokens, etc.)

5. **Features NOT Supported**:
   - Embeddings


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