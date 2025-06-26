FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Claude Code SDK from PyPI
RUN pip install --no-cache-dir claude-code-sdk

# Copy provider code
COPY providers/ /app/providers/
COPY config/ /app/config/
COPY custom_handler.py /app/custom_handler.py
COPY custom_handler.py /app/config/custom_handler.py

# Copy startup script, auth integration, and entrypoint
COPY startup.py /app/startup.py
COPY auth_integration.py /app/auth_integration.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create directory for Claude auth with proper permissions
RUN mkdir -p /root && chmod 755 /root

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:4000/health || exit 1

CMD ["/app/entrypoint.sh"]