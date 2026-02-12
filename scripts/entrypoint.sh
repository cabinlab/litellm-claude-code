#!/bin/bash
set -e

# 1. Call base image entrypoint for OAuth setup
/usr/local/bin/docker-entrypoint.sh true

# 2. Validate LITELLM_MASTER_KEY
if [ -z "$LITELLM_MASTER_KEY" ]; then
  echo "ERROR: LITELLM_MASTER_KEY is required." >&2
  echo "Generate one: echo \"sk-\$(openssl rand -hex 32)\"" >&2
  exit 1
fi
if [[ "$LITELLM_MASTER_KEY" != sk-* ]]; then
  echo "ERROR: LITELLM_MASTER_KEY must start with 'sk-' (LiteLLM requirement)." >&2
  exit 1
fi

# 3. Start LiteLLM proxy directly
exec litellm --config /app/config/litellm_config.yaml \
  --host 0.0.0.0 --port 4000
