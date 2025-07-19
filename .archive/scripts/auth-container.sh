#!/bin/bash

echo "==================================="
echo "Claude Code Container Authentication"
echo "==================================="
echo ""

# Check if container is running
if ! docker ps | grep -q litellm-claude-litellm-1; then
    echo "Error: Container 'litellm-claude-litellm-1' is not running."
    echo "Please start the container first with: docker-compose up -d"
    exit 1
fi

# Check current auth status
echo "Checking current authentication status..."
docker exec litellm-claude-litellm-1 claude-auth status

echo ""
echo "To authenticate, we'll open a browser window for OAuth login."
echo "This is an interactive process that requires you to log in to Claude."
echo ""
read -p "Press Enter to continue with authentication..."

# Run the OAuth login
echo ""
echo "Starting OAuth authentication..."
echo "A browser window should open. Please complete the login process."
echo ""

docker exec -it litellm-claude-litellm-1 claude-auth login

echo ""
echo "Checking authentication status..."
docker exec litellm-claude-litellm-1 claude-auth status

echo ""
echo "Authentication process complete!"
echo "The credentials are stored in a Docker volume and will persist across container restarts."