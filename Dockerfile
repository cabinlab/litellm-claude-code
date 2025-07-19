FROM ghcr.io/cabinlab/claude-code-sdk-docker:python

# Switch to root for installations
USER root

# Install LiteLLM and additional dependencies
RUN pip install --no-cache-dir \
    litellm[proxy]>=1.40.0 \
    prisma \
    aiofiles

# Generate Prisma client as root to avoid permission issues later
RUN cd /opt/venv/lib/python3.11/site-packages/litellm/proxy && \
    prisma generate || true

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