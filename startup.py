#!/usr/bin/env python3
"""
Startup script that generates Prisma client and starts LiteLLM
"""
import sys
import os
import subprocess

# Add paths for custom providers
sys.path.append('/app')

# The custom provider will be loaded via the YAML config
print("Starting LiteLLM with custom provider configuration...")

# Skip Prisma generation when running as non-root user
print("Skipping Prisma client generation (running as non-root user)")

print("Starting LiteLLM proxy with YAML config...")

if __name__ == "__main__":
    os.environ['CONFIG_FILE_PATH'] = '/app/config/litellm_config.yaml'
    
    # Check for required master key
    master_key = os.environ.get('LITELLM_MASTER_KEY')
    if not master_key:
        print("[STARTUP] ERROR: LITELLM_MASTER_KEY environment variable is required")
        print("[STARTUP] This key protects access to your authenticated Claude instance.")
        print("[STARTUP] ")
        print("[STARTUP] To set it:")
        print("[STARTUP] 1. Copy .env.example to .env and set your own key")
        print("[STARTUP] 2. Or set environment variable: LITELLM_MASTER_KEY=<your-key> docker-compose up")
        print("[STARTUP] ")
        print("[STARTUP] Generate a secure key: echo \"sk-$(openssl rand -hex 32)\"")
        print("[STARTUP] Or for development: export LITELLM_MASTER_KEY=\"sk-dev-test-key\"")
        sys.exit(1)
    
    # Validate key format
    if not master_key.startswith('sk-'):
        print("[STARTUP] ERROR: LITELLM_MASTER_KEY must start with 'sk-' (LiteLLM requirement)")
        print("[STARTUP] Current key does not match required format.")
        print("[STARTUP] ")
        print("[STARTUP] Examples of valid keys:")
        print("[STARTUP] - sk-dev-test-key (for development)")
        print("[STARTUP] - sk-$(openssl rand -hex 32) (for production)")
        sys.exit(1)
    
    # Import litellm and ensure custom provider is registered
    import litellm
    
    # Double-check provider registration
    if hasattr(litellm, 'custom_provider_map'):
        print(f"[STARTUP] Custom providers registered: {litellm.custom_provider_map}")
        print(f"[STARTUP] Number of providers: {len(litellm.custom_provider_map)}")
        for i, provider in enumerate(litellm.custom_provider_map):
            print(f"[STARTUP] Provider {i}: {provider.get('provider')}")
    else:
        print("[STARTUP] Warning: No custom_provider_map found")
    
    # Also check if our wrapper patch is applied
    print(f"[STARTUP] get_llm_provider function: {litellm.get_llm_provider}")
    
    import uvicorn
    from litellm.proxy.proxy_server import app
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=4000)