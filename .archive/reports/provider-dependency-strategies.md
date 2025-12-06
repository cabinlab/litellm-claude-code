# Provider Dependency Strategies Research Report

## Executive Summary

This report examines how LiteLLM providers and similar Python projects handle complex dependencies, particularly focusing on:
- Non-PyPI packages (like GitHub-hosted SDKs)
- System-level tools (like CLI requirements)
- Persistent authentication state
- Container-based services

The research provides actionable recommendations for handling the Claude Code SDK and CLI dependencies in the LiteLLM Claude provider.

## Key Findings

### 1. Non-PyPI Package Handling

#### Common Approaches

**Requirements.txt Format:**
```bash
# Standard PyPI packages
litellm>=1.0.0
requests>=2.28.0

# GitHub-hosted packages
git+https://github.com/arthurcolle/claude-code-sdk-python.git
git+https://github.com/user/package.git@v1.0.0
git+https://github.com/user/package.git@branch-name
```

**Setup.py Modern Approach (pip 19+):**
```python
setup(
    name='litellm-claude',
    install_requires=[
        'litellm>=1.0.0',
        'claude-code-sdk@git+https://github.com/arthurcolle/claude-code-sdk-python.git',
    ],
)
```

#### Real-World Examples

1. **GitGuardian's ggshield** - Uses GitHub-hosted dependencies for internal components
2. **MCP Atlassian** - Relies on GitHub-hosted MCP SDK with OAuth authentication
3. **LiteLLM Vertex AI Provider** - Uses Google's SDK which can be installed from GitHub or PyPI

### 2. System Dependencies & CLI Tools

#### Docker-Based Solutions

**Multi-Stage Builds Pattern:**
```dockerfile
# Stage 1: Install system dependencies
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Final image with CLI tools
FROM node:18-slim as node
FROM python:3.11-slim
COPY --from=node /usr/local/bin/node /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
```

#### Examples of CLI Tool Integration

1. **AWS Bedrock Provider** - Uses boto3 SDK with AWS CLI for authentication
2. **Google Vertex AI Provider** - Integrates with gcloud CLI for auth
3. **Azure Provider** - Can use Azure CLI for authentication alongside SDK

### 3. Authentication State Persistence

#### OAuth Token Storage Patterns

**Docker Volume Approach (MCP Atlassian Example):**
```bash
docker run --rm -i \
  -v "${HOME}/.mcp-atlassian:/home/app/.mcp-atlassian" \
  ghcr.io/sooperset/mcp-atlassian:latest
```

**Python OAuth Implementation (GitGuardian Pattern):**
```python
import os
import json
from pathlib import Path

class OAuthTokenManager:
    def __init__(self, config_dir=None):
        self.config_dir = config_dir or Path.home() / '.claude'
        self.token_file = self.config_dir / 'auth.json'
        
    def save_token(self, token_data):
        self.config_dir.mkdir(exist_ok=True)
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f)
            
    def load_token(self):
        if self.token_file.exists():
            with open(self.token_file, 'r') as f:
                return json.load(f)
        return None
```

### 4. Graceful Degradation Patterns

#### Optional Dependencies Pattern

**Basic Implementation:**
```python
# claude_code_provider.py
try:
    from claude_code import ClaudeCodeClient
    HAS_CLAUDE_SDK = True
except ImportError:
    HAS_CLAUDE_SDK = False
    import warnings
    warnings.warn(
        "Claude Code SDK not installed. Install with: "
        "pip install git+https://github.com/arthurcolle/claude-code-sdk-python.git",
        ImportWarning
    )

class ClaudeCodeProvider:
    def __init__(self):
        if not HAS_CLAUDE_SDK:
            raise ImportError(
                "Claude Code SDK is required. Please install it:\n"
                "pip install git+https://github.com/arthurcolle/claude-code-sdk-python.git"
            )
```

**Advanced Pattern with Feature Detection:**
```python
import subprocess
import shutil

class ClaudeCodeProvider:
    def __init__(self):
        self.has_sdk = self._check_sdk()
        self.has_cli = self._check_cli()
        
    def _check_sdk(self):
        try:
            import claude_code
            return True
        except ImportError:
            return False
            
    def _check_cli(self):
        return shutil.which('claude') is not None
        
    def authenticate(self):
        if self.has_cli:
            # Use CLI for OAuth flow
            subprocess.run(['claude', 'auth'])
        else:
            # Fall back to manual token entry
            print("Claude CLI not found. Please enter your auth token manually.")
```

## Recommendations for Claude Code Provider

### 1. Dependency Declaration Strategy

**Create pyproject.toml with optional dependencies:**
```toml
[project]
name = "litellm-claude"
dependencies = [
    "litellm>=1.0.0",
]

[project.optional-dependencies]
claude = [
    "claude-code-sdk@git+https://github.com/arthurcolle/claude-code-sdk-python.git",
]
dev = [
    "pytest>=7.0",
    "pytest-asyncio",
]

[project.urls]
repository = "https://github.com/user/litellm-claude"
```

### 2. Docker Strategy

**Enhanced Dockerfile:**
```dockerfile
# Install Node.js for Claude CLI
FROM node:18-slim as node

# Python base with system deps
FROM python:3.11-slim

# Copy Node.js for Claude CLI
COPY --from=node /usr/local/bin/node /usr/local/bin/
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules

# Install Claude CLI globally
RUN npm install -g @anthropic/claude-cli

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create volume mount point for auth persistence
RUN mkdir -p /root/.claude

# Copy application
COPY . .

# Volume for persistent auth
VOLUME ["/root/.claude"]
```

### 3. Authentication Handling

**Implement flexible authentication:**
```python
class ClaudeAuthManager:
    def __init__(self, auth_dir="/root/.claude"):
        self.auth_dir = Path(auth_dir)
        self.auth_file = self.auth_dir / "auth.json"
        
    def is_authenticated(self):
        return self.auth_file.exists() and self._validate_token()
        
    def authenticate(self):
        # Try CLI first
        if shutil.which('claude'):
            result = subprocess.run(['claude', 'auth'], capture_output=True)
            if result.returncode == 0:
                return True
                
        # Fall back to environment variable
        if token := os.getenv('CLAUDE_AUTH_TOKEN'):
            self.save_token({'token': token})
            return True
            
        # Manual entry as last resort
        return self._manual_auth()
```

### 4. Documentation Strategy

**Clear installation instructions:**
```markdown
## Installation

### Option 1: Docker (Recommended)
```bash
docker-compose up -d
```

### Option 2: Local Installation
```bash
# Install Claude Code SDK
pip install git+https://github.com/arthurcolle/claude-code-sdk-python.git

# Install Claude CLI (requires Node.js)
npm install -g @anthropic/claude-cli

# Install package
pip install -e .
```

### Authentication
The provider supports multiple authentication methods:
1. **Claude CLI** (preferred): `claude auth`
2. **Environment Variable**: `export CLAUDE_AUTH_TOKEN=your-token`
3. **Docker Volume**: Persists in `/root/.claude`
```

### 5. Error Handling

**Implement clear error messages:**
```python
class DependencyError(Exception):
    """Custom exception for missing dependencies"""
    pass

def check_dependencies():
    errors = []
    
    if not HAS_CLAUDE_SDK:
        errors.append(
            "Claude Code SDK not found. Install with:\n"
            "pip install git+https://github.com/arthurcolle/claude-code-sdk-python.git"
        )
        
    if not shutil.which('claude'):
        errors.append(
            "Claude CLI not found. Install with:\n"
            "npm install -g @anthropic/claude-cli"
        )
        
    if errors:
        raise DependencyError("\n\n".join(errors))
```

## Comparison with Other Providers

| Provider | Non-PyPI Deps | System Tools | Auth Persistence | Graceful Degradation |
|----------|---------------|--------------|------------------|---------------------|
| **AWS Bedrock** | boto3 (PyPI) | AWS CLI (optional) | ~/.aws/credentials | Falls back to env vars |
| **Vertex AI** | google-cloud (PyPI) | gcloud CLI | ADC or service account | Multiple auth methods |
| **Azure** | azure-sdk (PyPI) | Azure CLI (optional) | Environment vars | API key fallback |
| **Claude Code** | GitHub SDK | Claude CLI | Docker volume | Should implement fallbacks |

## Best Practices Summary

1. **Use optional dependencies** in pyproject.toml for clean separation
2. **Implement try/except ImportError** pattern for graceful degradation
3. **Use Docker volumes** for persistent authentication state
4. **Provide multiple authentication methods** (CLI, env vars, manual)
5. **Document all installation options** clearly with examples
6. **Create helpful error messages** that guide users to solutions
7. **Support both Docker and local** installation paths
8. **Test with and without** optional dependencies installed

## Conclusion

The Claude Code provider should follow established patterns from other LiteLLM providers while adapting to its unique requirements. The combination of optional dependencies, Docker volume persistence, and graceful degradation will create a robust solution that works in various deployment scenarios.