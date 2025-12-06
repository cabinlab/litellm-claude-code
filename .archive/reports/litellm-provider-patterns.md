# LiteLLM Custom Provider Patterns and Best Practices

## Executive Summary

This document provides comprehensive research on best practices for creating custom LiteLLM providers, based on official documentation, existing implementations, and analysis of the LiteLLM codebase. It includes specific recommendations for extracting and packaging the Claude Code provider as a standalone, reusable component.

## Table of Contents

1. [Provider Architecture Overview](#provider-architecture-overview)
2. [CustomLLM Implementation Pattern](#customllm-implementation-pattern)
3. [Authentication Patterns](#authentication-patterns)
4. [Configuration and Integration](#configuration-and-integration)
5. [Dependency Management](#dependency-management)
6. [Packaging and Distribution](#packaging-and-distribution)
7. [Best Practices Summary](#best-practices-summary)
8. [Recommendations for Claude Code Provider](#recommendations-for-claude-code-provider)

## Provider Architecture Overview

LiteLLM uses a plugin-based architecture that allows custom providers to integrate seamlessly with the framework. The key components are:

1. **CustomLLM Base Class**: Abstract base class that providers must extend
2. **Provider Registration**: Dynamic registration system using `custom_provider_map`
3. **Model Routing**: Convention-based routing using `provider-name/model-name` format
4. **Response Standardization**: Unified OpenAI-compatible response format

### Core Provider Structure

```python
from litellm import CustomLLM, ModelResponse
from litellm.types.utils import GenericStreamingChunk

class MyCustomProvider(CustomLLM):
    def completion(self, model: str, messages: List[Dict], **kwargs) -> ModelResponse:
        """Synchronous completion"""
        pass
    
    async def acompletion(self, model: str, messages: List[Dict], **kwargs) -> ModelResponse:
        """Asynchronous completion"""
        pass
    
    def streaming(self, model: str, messages: List[Dict], **kwargs) -> Iterator[GenericStreamingChunk]:
        """Synchronous streaming"""
        pass
    
    async def astreaming(self, model: str, messages: List[Dict], **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """Asynchronous streaming"""
        pass
```

## CustomLLM Implementation Pattern

### Required Methods

The `CustomLLM` class requires implementation of four core methods:

1. **completion()**: Synchronous text generation
2. **acompletion()**: Asynchronous text generation
3. **streaming()**: Synchronous streaming responses
4. **astreaming()**: Asynchronous streaming responses

### Optional Methods

Additional methods can be implemented for extended functionality:

1. **image_generation()**: Image generation support
2. **aimage_generation()**: Async image generation
3. **embedding()**: Text embeddings
4. **aembedding()**: Async embeddings

### Error Handling

Custom providers should raise `CustomLLMError` with appropriate status codes:

```python
from litellm.llms.custom_llm import CustomLLMError

class MyProvider(CustomLLM):
    def completion(self, *args, **kwargs):
        if not self.is_configured():
            raise CustomLLMError(
                status_code=500,
                message="Provider not properly configured"
            )
```

### Response Format

All methods must return responses in LiteLLM's standardized format:

```python
from litellm import ModelResponse, Usage, Choices, Message

def create_response(content: str, model: str) -> ModelResponse:
    response = ModelResponse()
    response.id = f"chatcmpl-{uuid.uuid4().hex}"
    response.object = "chat.completion"
    response.created = int(time.time())
    response.model = model
    response.choices = [Choices(
        finish_reason="stop",
        index=0,
        message=Message(content=content, role="assistant")
    )]
    response.usage = Usage(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    return response
```

## Authentication Patterns

LiteLLM supports multiple authentication patterns for custom providers:

### 1. API Key Authentication

Standard pattern using environment variables or configuration:

```python
class MyProvider(CustomLLM):
    def __init__(self):
        self.api_key = os.getenv("MY_PROVIDER_API_KEY")
```

### 2. OAuth Authentication

For OAuth-based services (like Claude Code SDK):

```python
class OAuthProvider(CustomLLM):
    def __init__(self):
        self.oauth_handler = OAuthHandler()
        self.token = self.oauth_handler.get_cached_token()
    
    async def refresh_token_if_needed(self):
        if self.oauth_handler.is_token_expired():
            self.token = await self.oauth_handler.refresh_token()
```

### 3. Custom Authentication

Implement custom authentication logic:

```python
from litellm.integrations.custom_auth_handler import CustomAuthHandler

class MyCustomAuth(CustomAuthHandler):
    def validate_request(self, request):
        # Custom validation logic
        return True
```

### 4. Integration with LiteLLM Auth

Custom providers can integrate with LiteLLM's authentication system:

```yaml
general_settings:
  custom_auth: custom_auth.my_auth_handler
  enable_jwt_auth: true
```

## Configuration and Integration

### Provider Registration

Providers must be registered in the `custom_provider_map`:

```python
import litellm

# Method 1: Direct registration
litellm.custom_provider_map = [
    {"provider": "my-provider", "custom_handler": MyProvider()}
]

# Method 2: Registration function
def register_provider():
    if not hasattr(litellm, 'custom_provider_map'):
        litellm.custom_provider_map = []
    
    litellm.custom_provider_map.append({
        "provider": "my-provider",
        "custom_handler": MyProvider()
    })
```

### YAML Configuration

For use with LiteLLM proxy server:

```yaml
model_list:
  - model_name: "my-model"
    litellm_params:
      model: "my-provider/model-name"
      custom_param: "value"

litellm_settings:
  custom_provider_map:
    - provider: "my-provider"
      custom_handler: custom_handler.provider_instance
```

### Model Routing

LiteLLM routes requests based on the model parameter format:

- `provider-name/model-name`: Routes to custom provider
- `custom/endpoint`: Routes to generic custom endpoint handler

### Parameter Handling

Custom parameters are passed via `optional_params`:

```python
def completion(self, model: str, messages: List[Dict], **kwargs):
    optional_params = kwargs.get("optional_params", {})
    custom_setting = optional_params.get("my_custom_param")
```

## Dependency Management

### Core Dependencies

Custom providers should minimize external dependencies. When required:

1. **Declare in requirements.txt**:
```txt
# Core provider dependencies
httpx>=0.27.0
pydantic>=2.0.0

# Provider-specific dependencies
my-special-sdk>=1.0.0
```

2. **Optional Dependencies in setup.py**:
```python
setup(
    name="litellm-my-provider",
    install_requires=[
        "litellm>=1.0.0",
        "httpx>=0.27.0",
    ],
    extras_require={
        "full": ["my-special-sdk>=1.0.0"],
    }
)
```

### Handling External SDKs

For providers requiring external SDKs (like Claude Code SDK):

```python
try:
    from external_sdk import Client
    HAS_SDK = True
except ImportError:
    HAS_SDK = False

class MyProvider(CustomLLM):
    def __init__(self):
        if not HAS_SDK:
            raise ImportError(
                "External SDK required. Install with: "
                "pip install external-sdk"
            )
```

### Version Compatibility

Ensure compatibility with LiteLLM versions:

```python
import litellm
from packaging import version

MIN_LITELLM_VERSION = "1.0.0"

if version.parse(litellm.__version__) < version.parse(MIN_LITELLM_VERSION):
    raise ImportError(f"LiteLLM {MIN_LITELLM_VERSION}+ required")
```

## Packaging and Distribution

### Package Structure

Recommended structure for a custom provider package:

```
litellm-my-provider/
├── README.md
├── setup.py
├── requirements.txt
├── litellm_my_provider/
│   ├── __init__.py
│   ├── provider.py
│   ├── auth.py
│   └── utils.py
├── examples/
│   ├── basic_usage.py
│   └── proxy_config.yaml
└── tests/
    ├── test_provider.py
    └── test_auth.py
```

### Setup.py Configuration

```python
from setuptools import setup, find_packages

setup(
    name="litellm-my-provider",
    version="0.1.0",
    author="Your Name",
    description="Custom LiteLLM provider for MyService",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/litellm-my-provider",
    packages=find_packages(),
    install_requires=[
        "litellm>=1.0.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio", "black", "flake8"],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
```

### Distribution Methods

1. **PyPI Distribution**:
```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

2. **GitHub Installation**:
```bash
pip install git+https://github.com/username/litellm-my-provider.git
```

3. **Local Development**:
```bash
pip install -e .
```

### Documentation Requirements

Essential documentation includes:

1. **README.md**: Installation, configuration, and basic usage
2. **API Reference**: Document all public methods and parameters
3. **Examples**: Working examples for common use cases
4. **Configuration Guide**: YAML configuration examples
5. **Troubleshooting**: Common issues and solutions

## Best Practices Summary

### 1. Code Organization

- Keep provider logic separate from authentication
- Use dependency injection for external services
- Implement proper error handling and logging
- Follow LiteLLM's response format strictly

### 2. Performance Optimization

- Implement connection pooling for HTTP clients
- Cache authentication tokens appropriately
- Use async methods for better concurrency
- Minimize blocking operations

### 3. Testing Strategy

- Unit tests for all provider methods
- Integration tests with mock services
- Test streaming functionality thoroughly
- Validate response format compliance

### 4. Security Considerations

- Never hardcode credentials
- Validate and sanitize all inputs
- Use secure token storage
- Implement rate limiting where appropriate

### 5. Maintenance

- Version your provider independently
- Document breaking changes clearly
- Maintain compatibility with multiple LiteLLM versions
- Provide migration guides for major updates

## Recommendations for Claude Code Provider

Based on this research, here are specific recommendations for extracting the Claude Code provider:

### 1. Package Structure

```
litellm-claude-code/
├── README.md
├── setup.py
├── requirements.txt
├── litellm_claude_code/
│   ├── __init__.py
│   ├── provider.py          # Main ClaudeCodeSDKProvider
│   ├── auth.py             # OAuth handling
│   ├── config.py           # Configuration management
│   └── exceptions.py       # Custom exceptions
├── examples/
│   ├── basic_usage.py
│   ├── streaming_example.py
│   ├── proxy_config.yaml
│   └── docker-compose.yml
├── tests/
│   ├── test_provider.py
│   ├── test_auth.py
│   └── test_streaming.py
└── docs/
    ├── installation.md
    ├── configuration.md
    └── troubleshooting.md
```

### 2. Key Improvements

1. **Authentication Module**: Extract OAuth logic into a separate module
2. **Token Persistence**: Implement configurable token storage
3. **Error Handling**: Add specific error types for common failures
4. **Configuration**: Support both environment variables and config files
5. **Logging**: Add comprehensive debug logging

### 3. Installation Options

```bash
# Basic installation
pip install litellm-claude-code

# With Claude SDK
pip install litellm-claude-code[claude]

# Development
pip install litellm-claude-code[dev]
```

### 4. Usage Patterns

**Direct Usage**:
```python
from litellm_claude_code import ClaudeCodeProvider
import litellm

# Register provider
provider = ClaudeCodeProvider()
litellm.custom_provider_map = [
    {"provider": "claude-code", "custom_handler": provider}
]

# Use with litellm
response = litellm.completion(
    model="claude-code/sonnet",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Proxy Configuration**:
```yaml
model_list:
  - model_name: "claude-sonnet"
    litellm_params:
      model: "claude-code/sonnet"

litellm_settings:
  custom_provider_map:
    - provider: "claude-code"
      custom_handler: litellm_claude_code.provider
```

### 5. Distribution Strategy

1. **Initial Release**: GitHub repository with installation instructions
2. **Beta Testing**: Gather feedback from early adopters
3. **PyPI Release**: Publish to PyPI for wider distribution
4. **Documentation**: Host on GitHub Pages or ReadTheDocs
5. **Community**: Create GitHub Discussions for support

This approach ensures the Claude Code provider follows LiteLLM best practices while remaining maintainable and easy to use.