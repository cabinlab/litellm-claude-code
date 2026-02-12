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
    chown -R claude:claude /home/claude/.cache

# Generate Prisma client
ENV PATH="/opt/venv/bin:$PATH"
RUN cd /opt/venv/lib/python3.11/site-packages/litellm/proxy && \
    PRISMA_PYTHON_CACHE_DIR=/home/claude/.cache/prisma-python prisma generate && \
    chown -R claude:claude /home/claude/.cache/prisma-python && \
    chown -R claude:claude /opt/venv/lib/python3.11/site-packages/prisma && \
    chmod -R 755 /opt/venv/lib/python3.11/site-packages/prisma

# Copy application code with proper ownership
COPY --chown=claude:claude providers/ /app/providers/
COPY --chown=claude:claude config/ /app/config/

# Copy entrypoint script
COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh
RUN chmod +x /app/scripts/entrypoint.sh

# Switch back to claude user
USER claude

# Working directory
WORKDIR /app

# Expose LiteLLM port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:4000/health || exit 1

# Single entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
