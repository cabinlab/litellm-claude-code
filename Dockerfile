FROM ghcr.io/cabinlab/claude-code-sdk-docker:python

# Switch to root for installations
USER root

# Install LiteLLM and additional dependencies
RUN pip install --no-cache-dir \
    litellm[proxy]>=1.40.0 \
    prisma \
    aiofiles

# Set up Prisma cache directory for claude user
ENV PRISMA_PYTHON_CACHE_DIR="/home/claude/.cache/prisma-python"
RUN mkdir -p /home/claude/.cache/prisma-python && \
    chown -R claude:claude /home/claude/.cache && \
    # Create a symlink from root's cache to claude's cache as a fallback
    mkdir -p /root/.cache && \
    ln -s /home/claude/.cache/prisma-python /root/.cache/prisma-python

# Generate Prisma client as root to avoid permission issues later
# First, ensure we're using the venv pip
ENV PATH="/opt/venv/bin:$PATH"
RUN cd /opt/venv/lib/python3.11/site-packages/litellm/proxy && \
    PRISMA_PYTHON_CACHE_DIR=/home/claude/.cache/prisma-python prisma generate && \
    # Ensure the claude user can access Prisma binaries
    chown -R claude:claude /home/claude/.cache/prisma-python && \
    chown -R claude:claude /opt/venv/lib/python3.11/site-packages/prisma && \
    chmod -R 755 /opt/venv/lib/python3.11/site-packages/prisma

# Copy application code with proper ownership
COPY --chown=claude:claude providers/ /app/providers/
COPY --chown=claude:claude config/ /app/config/
COPY --chown=claude:claude custom_handler.py /app/custom_handler.py
COPY --chown=claude:claude startup.py /app/startup.py

# Copy custom entrypoint that handles OAuth token setup
COPY scripts/litellm-entrypoint.sh /usr/local/bin/litellm-entrypoint.sh
RUN chmod +x /usr/local/bin/litellm-entrypoint.sh

# Switch back to claude user
USER claude

# Working directory
WORKDIR /app

# Expose LiteLLM port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:4000/health || exit 1

# Use custom entrypoint that chains Claude auth + LiteLLM startup
ENTRYPOINT ["/usr/local/bin/litellm-entrypoint.sh"]