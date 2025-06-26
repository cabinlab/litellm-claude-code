# Authentication Setup for LiteLLM Claude Code Provider

This guide explains how to authenticate the Claude CLI within the Docker container.

## Overview

⛔ ***Not Working*** The LiteLLM Claude Code Provider requires Claude CLI authentication to work. ~~We've integrated the authentication flow directly into the LiteLLM web interface for a seamless experience~~

## First-Time Setup

### Web Authentication (Currently 👎)

⚠️ The web authentication interface at `http://localhost:4000/auth` correctly displays authentication status but the interactive login flow is not yet fully functional. Please use the CLI method below for authentication.

### CLI Authentication (Recommended)

1. Start the container:
   ```bash
   docker-compose up -d
   ```

2. Access the container shell:
   ```bash
   docker exec -it litellm-claude-litellm-1 bash
   ```

3. Run the Claude CLI:
   ```bash
   claude
   ```

4. Follow the interactive prompts:
   - Choose your preferred theme (press Enter for default)
   - Select login method: Choose option 1 (Claude account with subscription)
   - The CLI will display an OAuth URL
   - Open the URL in your browser and authorize the application
   - Copy the authorization code and paste it back into the terminal

5. Exit the container shell:
   ```bash
   exit
   ```

6. Verify authentication by checking the web status page:
   ```
   http://localhost:4000/auth
   ```
   The status should show "Authenticated successfully!"

## Using the API

After authentication, you can:

1. **Access API Documentation**: http://localhost:4000/docs
2. **Make API Calls**:
   ```bash
   curl -X POST http://localhost:4000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-your-master-key" \
     -d '{
       "model": "sonnet",
       "messages": [{"role": "user", "content": "Hello Claude!"}]
     }'
   ```

## Persistence

- Authentication credentials are stored in a Docker volume named `claude-auth`
- Credentials persist across container restarts
- To remove authentication, delete the volume: `docker volume rm litellm-claude_claude-auth`
- You can also use /login /logout slash commands from within Claude Code if there's only one session

## Troubleshooting

### WebSocket Connection Failed
- Ensure you're accessing the page via HTTP (not HTTPS)
- Check that port 4000 is accessible
- Try refreshing the page

### Authentication Stuck
- The Claude CLI may be waiting for input
- Try restarting the container and retrying
- Check container logs: `docker-compose logs litellm`

### OAuth Page Shows Error
- This is normal - the CLI handles the callback internally
- Return to the authentication page to check status

## Security Notes

- Never expose port 4000 to the public internet without proper security
- Master keys must start with 'sk-' (LiteLLM requirement)
- Set your own master key via LITELLM_MASTER_KEY environment variable
- For production, use a secure randomly generated key

## Available Models

Once authenticated, you can use:
- `sonnet` - Claude Sonnet (latest)
- `opus` - Claude Opus (latest)
- `default` - Default model
- `claude-3-5-haiku-20240307` - Claude Haiku (latest, probably)