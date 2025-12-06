# Provider Distribution Models Research Report

## Executive Summary

This report examines distribution models for LiteLLM providers and similar plugin systems, with a focus on how to distribute the Claude Code provider to users who already have LiteLLM installed. The research covers provider architectures, distribution patterns, marketplace concepts, and practical approaches for handling complex runtime requirements.

## Key Findings

### 1. LiteLLM Provider Architecture

LiteLLM implements a flexible custom provider system with the following characteristics:

- **Custom Provider Mapping**: Uses `custom_provider_map` configuration to register providers dynamically
- **Model Routing**: Convention-based routing using `provider-name/model-name` format
- **CustomLLM Base Class**: Providers extend the `CustomLLM` class implementing standardized methods
- **YAML Configuration**: Supports both programmatic registration and YAML-based configuration

Example configuration:
```yaml
litellm_settings:
  custom_provider_map:
    - {"provider": "my-custom-llm", "custom_handler": custom_handler.my_custom_llm}
```

### 2. Distribution Models in the Ecosystem

#### 2.1 Direct PyPI Distribution

The standard approach for Python packages:

**Advantages:**
- Easy installation: `pip install litellm-claude-code`
- Version management through PyPI
- Dependency resolution handled automatically
- Integration with existing Python tooling

**Limitations:**
- Cannot include non-PyPI dependencies directly
- System-level dependencies require documentation
- No built-in handling for persistent state

#### 2.2 GitHub-Based Distribution

For providers with non-PyPI dependencies:

```bash
# Direct installation from GitHub
pip install git+https://github.com/user/litellm-claude-code.git

# With specific version/branch
pip install git+https://github.com/user/litellm-claude-code.git@v1.0.0
```

**Advantages:**
- Can include GitHub-hosted dependencies in requirements.txt
- Faster iteration without PyPI releases
- Direct access to development versions

**Example requirements.txt:**
```txt
litellm>=1.0.0
git+https://github.com/arthurcolle/claude-code-sdk-python.git
```

#### 2.3 Docker Container Distribution

For providers with complex runtime requirements:

```yaml
# docker-compose.yml
services:
  litellm-with-claude:
    image: ghcr.io/user/litellm-claude:latest
    volumes:
      - ./config:/app/config
      - claude-auth:/root/.claude
    ports:
      - "4000:4000"
```

**Advantages:**
- Includes all system dependencies (Node.js for Claude CLI)
- Persistent authentication via volume mounts
- Consistent environment across deployments
- No local installation required

#### 2.4 Plugin Marketplace Pattern

While LiteLLM doesn't have a formal marketplace, the pattern exists in similar systems:

**LangChain Model:**
- Standalone packages: `langchain-{provider}`
- Official vs community providers
- Standardized interfaces and testing

**OpenAI GPT Marketplace:**
- Evolved from plugin store to GPT marketplace
- Standardized manifest files
- Discovery and search capabilities

### 3. "Bring Your Own Provider" Patterns

#### 3.1 Drop-in Configuration

Users add provider to existing LiteLLM installation:

```python
# custom_providers.py
from litellm_claude_code import ClaudeCodeProvider

# Register the provider
claude_provider = ClaudeCodeProvider()
```

```yaml
# Add to existing litellm_config.yaml
litellm_settings:
  custom_provider_map:
    - provider: "claude-code"
      custom_handler: custom_providers.claude_provider
```

#### 3.2 Sidecar Pattern

Run provider as separate service:

```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main
    depends_on:
      - claude-provider
    
  claude-provider:
    image: ghcr.io/user/claude-provider:latest
    volumes:
      - claude-auth:/auth
```

#### 3.3 Extension Directory Pattern

Similar to VSCode extensions:

```
litellm_home/
├── providers/
│   ├── claude-code/
│   │   ├── __init__.py
│   │   ├── provider.py
│   │   └── manifest.json
│   └── other-provider/
```

### 4. Version Compatibility Strategies

#### 4.1 Semantic Versioning

```python
# setup.py
setup(
    name="litellm-claude-code",
    install_requires=[
        "litellm>=1.0.0,<2.0.0",  # Compatible with LiteLLM 1.x
    ],
)
```

#### 4.2 Feature Detection

```python
import litellm
from packaging import version

# Check LiteLLM version and features
if hasattr(litellm, 'custom_provider_map'):
    # Modern registration method
    pass
elif version.parse(litellm.__version__) >= version.parse("0.9.0"):
    # Legacy registration method
    pass
```

#### 4.3 Compatibility Matrix

Document supported versions:

| Provider Version | LiteLLM Version | Python Version |
|-----------------|-----------------|----------------|
| 1.0.x          | >=1.0.0,<2.0.0  | >=3.8         |
| 0.9.x          | >=0.9.0,<1.0.0  | >=3.7         |

### 5. Handling Special Runtime Requirements

#### 5.1 Optional Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
docker = ["docker-compose>=2.0"]
cli = ["claude-cli>=1.0"]
dev = ["pytest>=7.0", "black"]
```

#### 5.2 Runtime Checks

```python
class ClaudeCodeProvider:
    def __init__(self):
        self._check_dependencies()
    
    def _check_dependencies(self):
        # Check for Claude SDK
        try:
            import claude_code
        except ImportError:
            raise ImportError(
                "Claude Code SDK required. Install with:\n"
                "pip install 'litellm-claude-code[claude]'"
            )
        
        # Check for CLI (optional)
        if not shutil.which('claude'):
            warnings.warn(
                "Claude CLI not found. OAuth authentication unavailable.\n"
                "Install with: npm install -g @anthropic/claude-cli"
            )
```

#### 5.3 Graceful Degradation

```python
def authenticate(self):
    # Try OAuth via CLI
    if self.has_cli:
        return self._oauth_authenticate()
    
    # Fall back to API key
    if api_key := os.getenv('CLAUDE_API_KEY'):
        return self._api_key_authenticate(api_key)
    
    # Manual token entry
    return self._manual_authenticate()
```

## Recommended Distribution Strategy

### Primary: Docker Image with Pre-configured LiteLLM

```dockerfile
FROM ghcr.io/berriai/litellm:main

# Add Claude Code provider
RUN pip install git+https://github.com/user/litellm-claude-code.git

# Add Claude CLI
COPY --from=node:18-slim /usr/local/bin/node /usr/local/bin/
RUN npm install -g @anthropic/claude-cli

# Add configuration
COPY claude_config.yaml /app/config/
```

**Benefits:**
- Zero configuration for users
- All dependencies included
- Works with existing LiteLLM deployments

### Secondary: Standalone Package

```bash
# For users with existing LiteLLM
pip install litellm-claude-code

# With all dependencies
pip install litellm-claude-code[full]
```

**Installation Guide:**
```markdown
## Quick Start

### Option 1: Docker (Recommended)
```bash
docker run -d \
  -p 4000:4000 \
  -v $HOME/.claude:/root/.claude \
  ghcr.io/user/litellm-claude:latest
```

### Option 2: Add to Existing LiteLLM
```bash
pip install litellm-claude-code
```

Then add to your `litellm_config.yaml`:
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
```

### Tertiary: Provider Registry (Future)

Create a provider manifest format:

```json
{
  "name": "claude-code",
  "version": "1.0.0",
  "litellm_version": ">=1.0.0",
  "entry_point": "litellm_claude_code.provider",
  "dependencies": {
    "pip": ["git+https://github.com/arthurcolle/claude-code-sdk-python.git"],
    "system": ["node>=18.0.0"],
    "npm": ["@anthropic/claude-cli"]
  },
  "docker_image": "ghcr.io/user/litellm-claude:latest"
}
```

## Best Practices for Complex Providers

### 1. Clear Documentation

- Installation options (Docker, pip, manual)
- Dependency requirements
- Authentication setup
- Troubleshooting guide

### 2. Multiple Distribution Channels

- Docker Hub / GitHub Container Registry
- PyPI for pip installation  
- GitHub releases with binaries
- Pre-configured LiteLLM images

### 3. Dependency Management

- Use optional dependencies
- Provide clear error messages
- Support graceful degradation
- Document all requirements

### 4. Version Compatibility

- Test against multiple LiteLLM versions
- Use feature detection over version checks
- Maintain compatibility matrix
- Semantic versioning

### 5. User Experience

- Zero-config Docker option
- Clear upgrade paths
- Migration guides
- Example configurations

## Comparison: Distribution Models

| Model | Complexity | User Effort | Flexibility | Maintenance |
|-------|------------|-------------|-------------|-------------|
| **Docker Image** | Low | Minimal | Limited | Easy |
| **PyPI Package** | Medium | Moderate | High | Moderate |
| **GitHub Install** | Medium | Moderate | High | Easy |
| **Manual Setup** | High | High | Maximum | Hard |
| **Provider Registry** | Low | Minimal | Moderate | Complex |

## Conclusion

For the Claude Code provider with its unique requirements (OAuth, CLI tools, persistent state), a multi-channel distribution strategy is recommended:

1. **Primary**: Pre-built Docker images for zero-configuration deployment
2. **Secondary**: PyPI package with optional dependencies for advanced users
3. **Future**: Integration with a provider registry/marketplace when available

This approach ensures accessibility for all user types while maintaining the flexibility needed for complex authentication flows and system dependencies. The Docker-first strategy aligns with modern deployment practices and provides the best user experience for providers with non-standard requirements.