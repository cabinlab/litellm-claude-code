#!/bin/bash
set -e

echo "Starting LiteLLM Claude Code Provider..."

# Call the base image's entrypoint first to handle authentication setup
# This handles CLAUDE_CODE_OAUTH_TOKEN environment variable properly
if [ -f "/usr/local/bin/docker-entrypoint.sh" ]; then
    /usr/local/bin/docker-entrypoint.sh echo "Authentication setup complete"
fi

# Verify Claude CLI is accessible
if ! claude --version >/dev/null 2>&1; then
    echo "Warning: Claude CLI not accessible. Authentication may be required."
    echo "You can authenticate by running: docker exec -it litellm-claude-litellm-1 claude"
fi

# Set Python path
export PYTHONPATH="/app:$PYTHONPATH"

# Start LiteLLM via startup.py
echo "Starting LiteLLM server..."
exec python /app/startup.py